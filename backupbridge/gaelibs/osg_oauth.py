import urlparse

from google.appengine.api import urlfetch
from django.utils import simplejson

from gaelibs import oauth

class OSGOAuth(object):
    """
    Abstracting the oauth lib. Copied heavily from myspace MySpaceContext lib"
    """
    def __init__(self, consumer_key=None, consumer_secret=None,
            oauth_token_key=None, oauth_token_secret=None):
        self.consumer = oauth.OAuthConsumer(consumer_key, consumer_secret)
        self.signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self.last_response = None

        if oauth_token_key and oauth_token_secret:
            self.token = oauth.OAuthToken(oauth_token_key,
                    oauth_token_secret)
        else:
            self.token = None

    def _call_oauth_api(self, oauth_url, token=None, parameters=None,
            http_method="GET"):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
                self.consumer, token=token, http_url=oauth_url,
                parameters=parameters, http_method=http_method)
        oauth_request.sign_request(self.signature_method, self.consumer, token)
        resp = urlfetch.fetch(oauth_request.to_url(), method=http_method)
        self.last_response = resp
        if resp.status_code != 200:
            raise Exception("OAuth provider returned and error", resp.content)
        return resp.content

    def get_request_token(self, request_token_url=None, parameters=None,
            http_method="GET"):
        resp = self._call_oauth_api(request_token_url, parameters=parameters,
                http_method=http_method)
        token = oauth.OAuthToken.from_string(resp)
        return token

    def get_authorization_url(self, token, authorization_url=None,
            callback_url=None, parameters=None):
        oauth_request = oauth.OAuthRequest.from_token_and_callback(
                token=token, callback=callback_url, http_url=authorization_url)
        oauth_request.sign_request(self.signature_method, self.consumer, token)
        return oauth_request.to_url()

    def get_access_token(self, request_token, access_token_url=None,
            parameters=None, http_method="GET"):
        resp = self._call_oauth_api(access_token_url, token=request_token,
                parameters=parameters, http_method=http_method)
        token = oauth.OAuthToken.from_string(resp)
        return token

    def request(self, api_url, method="GET", parameters=None, body=None, raw_response=False):
        access_token = self.token
        
        http_method = "POST" if method in ["POST", "PUT"] else method
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
                self.consumer, token=access_token, http_method=http_method,
                http_url=api_url, parameters=parameters)
        oauth_request.sign_request(self.signature_method, self.consumer,
                access_token)

        headers = {}
        if method == "PUT":
            headers["X-HTTP-Method-Override"] = "PUT"

        if body is not None and http_method == "POST":
            body += "&".join(
                    "%s=%s" % (oauth.escape(str(k)),oauth.escape(str(v))) for k, v in parameters.iteritems())

        request_url = oauth_request.to_url()
        if http_method == "POST":
            qs = urlparse.urlparse(oauth_request.to_url()).query
            qparams = oauth_request._split_url_string(qs)
            qs = "&".join("%s=%s" % (oauth.escape(str(k)), oauth.escape(str(v))) for k, v in qparams.iteritems())
            request_url = oauth_request.get_normalized_http_url() + "?" + qs

        resp = urlfetch.fetch(request_url, payload=body, headers=headers,
                method=http_method)
        self.last_response = resp
        if resp.status_code > 201:
            raise Exception("API returned an error", resp.content)

        api_response = resp.content if raw_response else simplejson.loads(resp.content)
        return api_response

    @staticmethod
    def token_from_string(s):
        return oauth.OAuthToken.from_string(s)

    @staticmethod
    def to_token(key, secret=None):
        return oauth.OAuthToken(key, secret=secret)
