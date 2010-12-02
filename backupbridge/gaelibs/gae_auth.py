from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib.auth.models import AnonymousUser
from django.template import RequestContext

from gaelibs.gaesessions import get_current_session

import logging

class AuthenticationMiddleware(object):
    def process_request(self, request):
        assert hasattr(request, 'session'), 'Please enable gaelibs.gaesessions.DjangoSessionMiddleware in your MIDDLEWARE_CLASSES'
        User = dynamic_import_class_or_method("main_app.models.User")
        if not hasattr(request, "_cached_user"):
            session = get_current_session()
            if "user" in session:
                logging.info("we have user")
                user = User.get(str(session["user"]))
                request._cached_user = user
            else:
                request._cached_user = AnonymousUser()
        request.__class__.user = request._cached_user
        request.user = request._cached_user
        return None


def auth_context(request):
    def get_user():
        if hasattr(request, "user"):
            return request.user
        else:
            return AnonymousUser()
    user = get_user()
    return {'user': user}


def request_context(request):
    return {'request': request}


def dynamic_import_class_or_method(path):
    arr = path.split(".")
    klass = arr.pop()
    exec "from %s import %s as User" % (".".join(arr), klass)
    return User

def require_login(login_url):
    def decorator(view):
        def func(*args, **kwargs):
            if "user" in args[0].session and args[0].session["user"] is not None:
                return view(*args, **kwargs)
            else:
                return HttpResponseRedirect(login_url)
        return func
    return decorator

def login(request, user):
    request.session["user"] = str(user.key())
    request.session.save()


def logout(request):
    if "user" in request.session:
        del request.session["user"]
        request.session.clear()
        request.session.save()

def authenticate(username=None, password=None):
    User = dynamic_import_class_or_method(settings.AUTH_USER_MODEL)
    query = User.all()
    query.filter("username =", username)
    query.filter("password =", password)
    return query.get()
