# -*- coding: utf-8 -*-

import urllib2
import urllib
import logging
import oauth
from osg_oauth import OSGOAuth

import gdata.contacts
import gdata.contacts.service
import gdata.photos
import gdata.photos.service

GOOGLE_API_URL = "https://www.google.com"
GOOGLE_REQUEST_TOKEN_URL = "https://www.google.com/accounts/OAuthGetRequestToken"
GOOGLE_ACCESS_TOKEN_URL = "https://www.google.com/accounts/OAuthGetAccessToken"
GOOGLE_AUTHORIZE_URL = "https://www.google.com/accounts/OAuthAuthorizeToken"

class GoogleAuth(OSGOAuth):
    API_URL = "https://www.google.com"

    def __init__(self, consumer_key=None, consumer_secret=None,
            oauth_token_key=None, oauth_token_secret=None):
        super(GoogleAuth, self).__init__(consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                oauth_token_key=oauth_token_key,
                oauth_token_secret=oauth_token_secret)
        #if oauth_token_key is not None and oauth_token_secret is not None:
        #    self.user_profile = self.verify_credentials()

    def get_request_token(self, request_token_url=None, parameters=None):
        url = request_token_url if request_token_url is not None else GOOGLE_REQUEST_TOKEN_URL
        return super(GoogleAuth, self).get_request_token(url,
                parameters=parameters)

    def get_authorization_url(self, token, authorization_url=None, callback_url=None):
        url = authorization_url if authorization_url is not None else GOOGLE_AUTHORIZE_URL
        return super(GoogleAuth, self).get_authorization_url(token, url, callback_url)

    def get_access_token(self, request_token, access_token_url=None, parameters=None):
        url = access_token_url if access_token_url is not None else GOOGLE_ACCESS_TOKEN_URL
        return super(GoogleAuth, self).get_access_token(request_token, url, parameters=parameters)


    def google_api(self, resource, params=None):
        return self.request(self.API_URL + resource, parameters=params)

    def request(self, api_url, method="GET", parameters=None, body=None,
            raw_response=False, gdata_service=None, converter=None):
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

        resp = gdata_service.GetFeed(request_url, extra_headers=headers,
                converter=converter)

        return resp


class GoogleContacts(GoogleAuth):
    API_URL = "https://www.google.com"

    def get_profile(self):
        res = self.google_api('/m8/feeds/contacts/default/full')
        return {'name': res.author[0].name.text,
                'email': res.author[0].email.text}
        

    def get_contacts(self):
        res = self.google_api('/m8/feeds/contacts/default/full')
        max_results = res.total_results.text
        return self.google_api('/m8/feeds/contacts/default/full',
                {'max-results': max_results})

    def request(self, api_url, method="GET", parameters=None, body=None,
            raw_response=False):
        return super(GoogleContacts, self).request(api_url, method, parameters, body,
                raw_response, gdata.contacts.service.ContactsService(),
                gdata.contacts.ContactsFeedFromString)

        
class PicasaWeb(GoogleAuth):
    API_URL = "https://picasaweb.google.com"

    def get_profile(self):
        res = self.google_api('/data/feed/base/user/default', {'kind':'album'})
        return {'name': res.author[0].name.text,
                'uri': res.author[0].uri.text}

    def google_api(self, resource, params=None,
            converter=gdata.photos.AnyFeedFromString):
        return self.request(self.API_URL + resource, parameters=params,
                converter=converter)

    def request(self, api_url, method="GET", parameters=None, body=None,
            raw_response=False, converter=gdata.photos.AnyFeedFromString):
        access_token = self.token
        if parameters is None:
            parameters = {'max-results': 10000}

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

        req = urllib2.Request(request_url, data=body, headers=headers)
        resp = urllib2.urlopen(req)

        self.last_response = resp

        resp_content = resp.read()
        if resp.code > 201:
            raise Exception('API returned an error', resp_content)
        
        #print "%s" % resp_content

        feed = converter(resp_content)

        return feed
