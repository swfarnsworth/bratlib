def except_return(alternative, *exceptions):

    def wrap(func):

        def _wrap(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions:
                return alternative

        return _wrap

    return wrap


# Decorator to streamline comparison operator implementations
return_not_implemented = except_return(NotImplemented, AttributeError)