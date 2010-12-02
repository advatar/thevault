import urllib
import logging
from gaelibs import oauth
from gaelibs.osg_oauth import OSGOAuth
import gdata.contacts
import gdata.contacts.service

GOOGLE_API_URL = "https://www.google.com"
GOOGLE_REQUEST_TOKEN_URL = "https://www.google.com/accounts/OAuthGetRequestToken"
GOOGLE_ACCESS_TOKEN_URL = "https://www.google.com/accounts/OAuthGetAccessToken"
GOOGLE_AUTHORIZE_URL = "https://www.google.com/accounts/OAuthAuthorizeToken"

class GoogleAuth(OSGOAuth):

    def __init__(self, consumer_key=None, consumer_secret=None,
            oauth_token_key=None, oauth_token_secret=None):
        super(self.__class__, self).__init__(consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                oauth_token_key=oauth_token_key,
                oauth_token_secret=oauth_token_secret)
        #if oauth_token_key is not None and oauth_token_secret is not None:
        #    self.user_profile = self.verify_credentials()

    def get_request_token(self, request_token_url=None, parameters=None):
        url = request_token_url if request_token_url is not None else GOOGLE_REQUEST_TOKEN_URL
        return super(self.__class__, self).get_request_token(url,
                parameters=parameters)

    def get_authorization_url(self, token, authorization_url=None, callback_url=None):
        url = authorization_url if authorization_url is not None else GOOGLE_AUTHORIZE_URL
        return super(self.__class__, self).get_authorization_url(token, url, callback_url)

    def get_access_token(self, request_token, access_token_url=None, parameters=None):
        url = access_token_url if access_token_url is not None else GOOGLE_ACCESS_TOKEN_URL
        return super(self.__class__, self).get_access_token(request_token, url, parameters=parameters)

    def get_contacts(self):
        res = self.google_api('/m8/feeds/contacts/default/full')
        logging.debug(res)
        max_results = res.total_results.text
        return self.google_api('/m8/feeds/contacts/default/full',
                {'max-results': max_results})

    def google_api(self, resource, params=None):
        return self.request(GOOGLE_API_URL + resource, parameters=params)

    def request(self, api_url, method="GET", parameters=None, body=None,
            raw_response=False, gdata_service=None):
        access_token = self.token

        http_method = "POST" if method in ["POST", "PUT"] else method
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
                self.consumer, token=access_token, http_method=http_method,
                http_url=api_url, parameters=parameters)
        oauth_request.sign_request(self.signature_method, self.consumer,
                access_token)
        
        headers = oauth_request.to_header()

        request_url = oauth_request.to_url()

        if method == "PUT":
            headers["X-HTTP-Method-Override"] = "PUT"

        if body is not None and http_method == "POST":
            body += "&".join(
                    "%s=%s" % (oauth.escape(str(k)),oauth.escape(str(v))) for k, v in parameters.iteritems())

        if http_method == "POST":
            qs = urlparse.urlparse(oauth_request.to_url()).query
            qparams = oauth_request._split_url_string(qs)
            qs = "&".join("%s=%s" % (oauth.escape(str(k)), oauth.escape(str(v))) for k, v in qparams.iteritems())
            request_url = oauth_request.get_normalized_http_url() + "?" + qs
        else:
            if parameters:
                request_url = "%s?%s" % (oauth_request.http_url, urllib.urlencode(parameters))
            else:
                request_url = oauth_request.http_url

        client = gdata_service or gdata.contacts.service.ContactsService()

        resp = client.GetFeed(request_url, extra_headers=headers,
                converter=gdata.contacts.ContactsFeedFromString)
        return resp

