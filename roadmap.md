# Roadmap

This document describes planned changes to the package.

## Python versions

For each Python version listed here, the changes described are those that will be made for
the first release that stops supporting earlier Python versions.

- 3.8
    - `cached-property` can be deleted as a dependency and replaced with `functools.cached_property`.
    - Error messages can use `f'{var=}'` syntax to more clearly communicate which variables were part of an error.
- 3.9
    - Type aliases like `t.List` can be replaced with the actual type.
  