from itertools import chain
concat = chain.from_iterable

_getattr = object.__getattribute__
_setattr = object.__setattr__

class OverlayProxy:
    """Read-Only overlay proxy object; this allows you to access
    the attributes from a number of objects as if they where objects.
    Create by calling the constructor with a variadic list of objects
    to overlay.

    Then, if an attribute is red, we will look inside the first object
    specified; if it has the attribute, we return that, otherwise we go
    on to the next object until we tried all of them.

    Thread safe, after creation. """
    # TODO: Complain about duplicates

    def __init__(self, *objs):
        _setattr(self, "objs", list(objs))

    def __getattribute__(self, name):
        objs = _getattr(self, "objs")
        for p in objs:
            try:
                return getattr(p, name)
            except AttributeError:
                pass

        raise AttributeError(
            "No such attribute '" + str(name) + "' in any of " + repr(objs))

    def __dir__(self):
        objs = _getattr(self, "objs")
        return set(concat(map(dir, objs)))

    def __setattr__(self, name, val):
        return TypeError("Writing not supported by " + self.name)

    def __delattr__(self, name):
        return TypeError("Writing not supported by " + self.name)
