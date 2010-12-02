import logging
from functools import update_wrapper
from werkzeug.exceptions import (
        MethodNotAllowed, Unauthorized,)

def log_wrapper(func):
    """
    Logs when function is entered an exited.
    Handy for debugging.
    """
    def inner(*args, **kwargs):
        logging.debug("in %s", func.__name__)
        logging.debug("args: %r", args)
        logging.debug("kwargs: %r", kwargs)
        res = func(*args, **kwargs)
        logging.debug("returns %r", res)
        logging.debug("out %s", func.__name__)
        return res
    update_wrapper(inner, func)
    return inner


def restrict_to_methods(*methods):
    """
    Only allow specific HTTP request method to access a view.
    Does away with things like `if request.method == 'GET'` in
    view code at the expense of having extra views to handle form
    submission.
    """
    def outer(func):
        def inner(request, *args, **kwargs):
            if not request.method in methods:
                return MethodNotAllowed('Method not allowed')
            return func(request, *args, **kwargs)
        update_wrapper(inner, func)
        return inner
    return outer

def require_login(func):
    """
    Basically the same as kay's login_required decorator but
    returns an Unauthorized exception to the browser rather than
    redirecting to the login page.
    """
    def inner(request, *args, **kwargs):
        if request.user.is_anonymous():
            return Unauthorized()
        return func(request, *args, **kwargs)
    update_wrapper(inner, func)
    return inner
