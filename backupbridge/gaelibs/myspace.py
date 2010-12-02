from gaelibs.osg_oauth import OSGOAuth
from gaelibs.oauth import OAuthConsumer
import logging
import time

MYSPACE_API_URL = "http://api.myspace.com/v2"
MYSPACE_REQUEST_TOKEN_URL = "http://api.myspace.com/request_token"
MYSPACE_ACCESS_TOKEN_URL = "http://api.myspace.com/access_token"
MYSPACE_AUTHORIZE_URL = "http://api.myspace.com/authorize"

class Myspace(OSGOAuth):
    
    def __init__(self, consumer_key=None, consumer_secret=None,
            oauth_token_key=None, oauth_token_secret=None):
        super(self.__class__, self).__init__(consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                oauth_token_key=oauth_token_key,
                oauth_token_secret=oauth_token_secret)
        if oauth_token_key and oauth_token_secret:
            self.token = OAuthConsumer(oauth_token_key, oauth_token_secret)
        else:
            self.token = None          
        

    def get_request_token(self, request_token_url=None):
        url = request_token_url if request_token_url is not None else MYSPACE_REQUEST_TOKEN_URL
        return super(self.__class__, self).get_request_token(url)

    def get_authorization_url(self, token, authorization_url=None, callback_url=None):
        url = authorization_url if authorization_url is not None else MYSPACE_AUTHORIZE_URL
        return super(self.__class__, self).get_authorization_url(token, url, callback_url)

    def get_access_token(self, request_token, access_token_url=None):
        url = access_token_url if access_token_url is not None else MYSPACE_ACCESS_TOKEN_URL
        return super(self.__class__, self).get_access_token(request_token, url)

    def myspace_api(self, resource, params=None):
        return self.request(MYSPACE_API_URL + resource, parameters=params)
        
    def get_profile(self):
        return self.myspace_api('/people/@me/@self')

    def get_friends(self, start=None, count=None):
        parameters = {'startIndex': start or 1,
                'count': count or 20,
                'sortBy': 'updated'}

        return self.myspace_api("/people/@me/@friends", parameters)

    def get_all_friends(self):
        friends = []
        try:
            done = False
            start = 1
            while not done:
                res = self.get_friends(start)
                done = (int(res['startIndex']) * int(res['itemsPerPage'])) >= int(res['totalResults'])
                friends.extend(res['entry'])
                start = start + 1

        except Exception, e:
            logging.debug(e)
        finally:
            return friends

