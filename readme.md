# What is it

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

## Running

To run, enter the python console and `import wild`.

## Motivation

This method could be helpful in order to maintain a specific
naming scheme: It allows you to consistently address all
contents of `wild.` through the wild package.

`from wild import talk`
`import wild; wild.talk`

At the moment part's of the wild package would have to fall
back to importing specific subparts of wild, which may be
undesirable because:

* it may be inconsistent with the rest of your application
* wild is only split into parts in order to have shorter files
* it generates more effort when refactoring (you have to change all the imports)

The specific case for which I am considering this structure
is this:

There are multiple packages: wild, calm, mood, anger. All of
those are implementations of the same interface and they are
based on each other: all of the packages are based on mood
and anger is based on wild.
This has the effect that classes and functions with the same
names from wild, mood and anger will be used in the anger
package.
This makes keeping track of which specific version we are
currently using very hard; by using the namespace prefixes
explicitly this problem is alleviated a bit.

The usual solution would be to address the elements of the
current package without prefix (addressing anger.talk inside
anger using just `talk`). This would work as a rule, but in
my opinion using `anger.` explicitly makes the code
considerably more easy to read.
