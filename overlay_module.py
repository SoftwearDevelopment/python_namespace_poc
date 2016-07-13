from sys import modules
from importlib.util import find_spec, module_from_spec
from overlay_proxy import OverlayProxy

_getattr = object.__getattribute__
_setattr = object.__setattr__

class _LazyModule:
    value = None
    package = None

    def __init__(self, name, package=None):
        _setattr(self, "module", name)
        _setattr(self, "package", package)

    def __getattribute__(self, a):
        inner = _getattr(self, "_get_value")()
        return getattr(inner, a)

    def __setattr__(self, a, v):
        inner = _getattr(self, "_get_value")()
        return setattr(inner, a, v)

    def __dir__(self):
        inner = _getattr(self, "_get_value")()
        return _getattr(inner, "__dir__")()

    def _get_value(self):
        if not _getattr(self, "value"):
            _getattr(self, "_load")()
        return _getattr(self, "value")

    def _load(self):
        spec = find_spec(
            name=_getattr(self, "module"),
            package=_getattr(self, "package"))
        l = module_from_spec(spec)
        _setattr(self, "value", l)
        spec.loader.exec_module(l)


class OverlayModule:
    def __init__(self, name, *mods):
        m = modules[name] # The real module

        # These are all the submodules we plan to load
        lazys = [_LazyModule(m, package=name) for m in mods]

        # The overlay proxy acts as a surrogate module while we are loading;
        # we include the module itself so we also export the components of
        # it; for some special properties, like __spec__ this is actually
        # very important; since __spec__ is accessed while loading submodules,
        # not providing it would trigger an infinite recursion.
        # For some other properties like __doc__ or __name__ this provides
        # correctness.
        p = OverlayProxy(m, *lazys)
        modules[name] = p

        # Until this point no action has been applied; we just set up our
        # proxy so it will start loading once we actually load data.
        # Using dir() triggers that all the modules are loaded; this works
        # because ObjectProxy.dir will call dir on each of the LazyModules,
        # which in turn will trigger the LazyModule to actually be loaded.
        #
        # Now, the tricky part is this: When a submodule "SUB" we're loading
        # imports the base module (let's call it WILD) and accesses some
        # property P on WILD, the ObjectProxy's __getattribute__ will try
        # getattr() on each of the lazy modules sequentially.
        #
        # For loaded modules this will simply lookup and retrieve the value
        # or throw an error if it's missing.
        #
        # If the value isn't however in any of the modules that have been
        # loaded already, getattr will be called on SUB itself:
        # SUB will be treated like it is already loaded (see LazyModule for
        # details), so we look up if the property is there – this enables
        # constructs like defining a class and in the next line accessing
        # it through the parent module.
        #
        # Now we searched for the property in question (named still P) in all
        # the modules we previously loaded and in the module we are currently
        # loading.
        # This was unsuccessful, so we now start loading all the rest of the
        # module and try finding P.
        # No special logic is used for this, ObjectProxy is still just calling
        # getprop, triggering the LazyModule to perform the actual load,
        # if this has not been done in the past.
        #
        # At some point we may find P in some of the submodules we're loading,
        # in this case __getattribute__ in ObjectProxy will be satisfied it
        # found the property and return it thus allowing the module SUB we
        # where initially trying to execute to continue.
        #
        # This can happen recursively: You may have some property Q from
        # third module "C" in the list required in the first "A" and second "A".
        # In this case both A and B would be executed recursively and stopped
        # at the points where the Q is required.
        # Your stack would look something like this at the point where Q is
        # actually being set:
        #
        # (Omitting all of python's import methods in between)
        # STACK FRAME  SOURCE FILE           METHOD                            CODE                                             MORE READABLE TRANSLATION OF CODE
        #           0  wild/C.py:                                              > Q = "Hello World"
        #           1  overlay_module.py:    _LazyModule._load                 > spec.loader.exec_module(C)                     "import C"
        #           2  overlay_module.py:    _LazyModule._get_value            > _getattr(self, "_load")()                      "load()"
        #           3  overlay_module.py:    _LazyModule.__getattribute__      > inner = _getattr(self, "_get_value")()         "inner = self._get_value()"
        #           4  overlay_proxy.py:     OverlayProxy.__getattribute__     > return getattr(p, name)
        #           5  wild/B.py:                                              > print("Can access Q in wild/B.py: ", wild.Q)
        #           6  overlay_module.py:    _LazyModule._load                 > spec.loader.exec_module(B)                     "import B"
        #           7  overlay_module.py:    _LazyModule._get_value            > _getattr(self, "_load")()                      "load()"
        #           8  overlay_module.py:    _LazyModule.__getattribute__      > inner = _getattr(self, "_get_value")()         "inner = self._get_value()"
        #           9  overlay_proxy.py:     OverlayProxy.__getattribute__     > return getattr(p, name)
        #          10  wild/A.py:                                              > print("Can access Q in wild/A.py: ", wild.Q)
        #          11  overlay_module.py:    _LazyModule._load                 > spec.loader.exec_module(B)                     "import A"
        #          12  overlay_module.py:    _LazyModule._get_value            > _getattr(self, "_load")()                      "load()"
        #          13  overlay_module.py:    _LazyModule.__dir__               > inner = _getattr(self, "_get_value")()         "inner = self._get_value()"
        #          14  overlay_proxy.py:     OverlayProxy.__dir__              > return set(concat(map(dir, objs)))
        #          15  overlay_module.py:    OverlayModule.__init__            > for a in dir(p "_load"):
        #          16  wild/__init__.py:                                       > OverlayModule(globals()['__name__'], ".A", ".B", ".C", ".D")
        #          17  "<stdin>" (command line):                               > import wild
        #
        # Finally: Both circular dependencies and properties will simply throw
        # an error "not found".
        for a in dir(p):
            # So we can get rid of the proxy we copy all the
            # values from the overlay into the module itself;
            # properties like __spec__ will be taken from the
            # module itself, so they will be overwritten with
            # themselves
            setattr(m, a, getattr(p, a))

        # Finally, export the proper module with the copied values
        modules[name] = m
