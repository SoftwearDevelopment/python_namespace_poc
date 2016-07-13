This is a little demo showing how consistent namespaces can
be used.

Specifically, this addresses the following situations.

```
wild/
  __init__.py
  A.py
  B.py
  C.py

* Everything in wild/* should be exported in the wild package
* The modules wild.A, wild.B and wild.C depend on each other
  (in a non circular way); they should be able to access
  each other's properties using the wild. namespace
* This should work:

C.py:
  import wild
  var_from_C = 42
  print(wild.var_from_C)
```

see OverlayModule and `wild/__init__.py` on how this is
achieved.

To run, enter the python console and `import wild`.
