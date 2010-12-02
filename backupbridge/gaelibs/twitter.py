from gaelibs.osg_oauth import OSGOAuth

TWITTER_API_URL = "https://api.twitter.com/1"
TWITTER_REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
TWITTER_ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"
TWITTER_AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize"
TWITTER_AUTHENTICATE_URL = "https:/api.twitter.com/oauth/authenticate"

class Twitter(OSGOAuth):

    def __init__(self, consumer_key=None, consumer_secret=None,
            oauth_token_key=None, oauth_token_secret=None):
        super(self.__class__, self).__init__(consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                oauth_token_key=oauth_token_key,
                oauth_token_secret=oauth_token_secret)
        if oauth_token_key is not None and oauth_token_secret is not None:
            self.user_profile = self.verify_credentials()

    def get_request_token(self, request_token_url=None, parameters=None):
        url = request_token_url if request_token_url is not None else TWITTER_REQUEST_TOKEN_URL
        return super(self.__class__, self).get_request_token(url,
                parameters=parameters)

    def get_authorization_url(self, token, authorization_url=None, callback_url=None):
        url = authorization_url if authorization_url is not None else TWITTER_AUTHORIZE_URL
        return super(self.__class__, self).get_authorization_url(token, url, callback_url)

    def get_access_token(self, request_token, access_token_url=None, parameters=None):
        url = access_token_url if access_token_url is not None else TWITTER_ACCESS_TOKEN_URL
        return super(self.__class__, self).get_access_token(request_token, url, parameters=parameters)

    def twitter_api(self, resource, params=None):
        return self.request(TWITTER_API_URL + resource, parameters=params)

    def verify_credentials(self):
        return self.twitter_api("/account/verify_credentials.json", None)

    def home_timeline(self, params=None):
        return self.twitter_api("/statuses/home_timeline.json", params)

    def friends_timeline(self, params=None):
        return self.twitter_api("/statuses/friends_timeline.json", params)

    def user_timeline(self, params=None):
        return self.twitter_api("/statuses/user_timeline.json", params)

    def public_timeline(self, params=None):
        return self.twitter_api("/statuses/public_timeline.json", params)

    def mentions(self, params=None):
        return self.twitter_api("/statuses/mentions.json", params)

    def retweeted_by_me(self, params=None):
        return self.twitter_api("/statuses/retweeted_by_me.json", params)

    def retweeted_to_me(self, params=None):
        return self.twitter_api("/statuses/retweeted_to_me.json", params)

    def update(self, message=None):
        if message is None:
            raise Exception("Twitter update must have a message")
        return self.twitter_api("/statuses/update.json", {"message": message})

    def friends(self, params=None):
        return self.twitter_api("/statuses/friends.json", params)

    def followers(self, params=None):
        return self.twitter_api("/statuses/followers.json", params)

    def all_friends(self):
        cursor = self.friends({'cursor':'-1'})
        friend_list = cursor['users']
        while(cursor['next_cursor'] != 0):
            cursor = self.friends({'cursor': cursor['next_cursor']})
            friend_list.extend(cursor['users'])
        return friend_list

    def all_followers(self):
        cursor = self.followers({'cursor': '-1'})
        follower_list = cursor['users']
        while(cursor['next_cursor'] != 0):
            cursor = self.follower({'cursor': cursor['next_cursor']})
            follower_list.extend(cursor['users'])
        return follower_list

    def follow(self, screen_name=None):
        if screen_name is None:
            raise Exception("Please provide the user screen name to follow")
        return self.twitter_api("/friendships/create.json", 
                {"screen_name": screen_name})

    def is_following(self, screen_name):
        if screen_name is None:
            raise Exception("Provide a screen_name to check for following")

        return self.twitter_api("/friendships/exists.json",
                {"user_a": self.user_profile["screen_name"], "user_b": screen_name})

