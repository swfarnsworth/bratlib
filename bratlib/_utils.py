def _except_return(alternative, *exceptions):

    def wrap(func):

        def _wrap(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions:
                return alternative

        return _wrap

    return wrap


# Decorator to streamline comparison operator implementations
_notimp = _except_return(NotImplemented, AttributeError)