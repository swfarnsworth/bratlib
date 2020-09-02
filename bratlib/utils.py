def except_return(alternative, *exceptions):

    def wrap(func):

        def _wrap(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions:
                return alternative

        return _wrap

    return wrap
