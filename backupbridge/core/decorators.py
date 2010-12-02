import urllib
import logging
from functools import update_wrapper

from werkzeug.exceptions import BadRequest, MethodNotAllowed

from gaelibs.oauth import (
    OAuthError, OAuthRequest, OAuthServer,
    OAuthSignatureMethod_PLAINTEXT,
    OAuthSignatureMethod_HMAC_SHA1,)

def oauth_protect(func):
    """
    Protect a resource with OAuth
    """
    from core.models import OAuthDataStore

    def inner(request, *args, **kwargs):
        try:
            oauth_request = OAuthRequest.from_request(request.method,
                    request.url, headers=request.headers,
                    query_string=urllib.urlencode(request.values))
            oauth_server = OAuthServer(OAuthDataStore())
            oauth_server.add_signature_method(OAuthSignatureMethod_PLAINTEXT())
            oauth_server.add_signature_method(OAuthSignatureMethod_HMAC_SHA1())

            consumer, token, params = oauth_server.verify_request(oauth_request)
            request.consumer = consumer
            request.token = token
            request.oauth_params = params
            return func(request, *args, **kwargs)
        except OAuthError, e:
            logging.debug(e)
            logging.debug(e.message)
            return BadRequest("%s" % e.message)
        except Exception, e:
            logging.debug(e)
            logging.debug(e.message)
            return BadRequest('Missing OAuth parameters')
    update_wrapper(inner, func)
    return inner

