from google.appengine.ext import db
from django.utils import simplejson as json

from kay.utils import url_for
from kay.ext.testutils.gae_test_base import GAETestBase
from kay.utils.test import Client

from werkzeug import BaseResponse, Request
from kay.app import get_application
from kay.utils.test import (
        init_recording, get_last_context,
        get_last_template, disable_recording,)
from kay.conf import settings

import cgi
import urllib
import logging

#logging.basicConfig(filename="test.log", level=logging.DEBUG)

from gaelibs.osg_oauth import OSGOAuth
from gaelibs.oauth import OAuthToken

class CoreTest(GAETestBase):
    def setUp(self):
        init_recording()
        app = get_application()
        self.client = Client(app, BaseResponse)
        self.consumer_key = "3db2991a3bd1f2ca292a463744f4136d61b1faa3"
        self.consumer_secret = "ee49886656eacc1451a1a06ad61d7a8b31448650"

    def tearDown(self):
        disable_recording()

    def test_fetch_oauth_request_token(self):
        osg_auth = OSGOAuth(self.consumer_key, self.consumer_secret)
        logging.debug("testing fetch request token")
        token = osg_auth.get_request_token("http://localhost:8080%s" % url_for('core/oauth/request_token'))
        #response = self.client.get(url)
        logging.debug("token.key: %r", token.key)
        logging.debug("token.secret: %r", token.secret)
        osg_auth = OSGOAuth(self.consumer_key,
                self.consumer_secret,
                token.key,
                token.secret)
        auth_url = osg_auth.get_authorization_url(token=token,
                authorization_url=("http://localhost:8080%s" % url_for('core/oauth/authorize')))
        logging.debug(auth_url)
        self.assertTrue(True)

    def test_fetch_oauth_access_token(self):
        token_string = "oauth_verifier=99702663&oauth_token=6e21fce62b88ee824118ee6f3d791d78a748f9a5"
        authorized_token = dict(cgi.parse_qsl(token_string))
        oauth_token = authorized_token.get('oauth_token')

        from google.appengine.api import urlfetch

        response = urlfetch.fetch("http://localhost:8080%s" %
                url_for('core/oauth/test_request_token', oauth_token=oauth_token))
        logging.debug(response.content)
        request_token = dict(cgi.parse_qsl(response.content))
        logging.debug(request_token)
        token = OAuthToken(request_token['oauth_token'], request_token['oauth_token_secret'])
        token.set_verifier(authorized_token['oauth_verifier'])

        osg_auth = OSGOAuth(self.consumer_key, self.consumer_secret)
        access_token = osg_auth.get_access_token(token, access_token_url="http://localhost:8080%s" % url_for('core/oauth/access_token'))
        logging.debug("access_token: %r", access_token.key)
        logging.debug("access_token_secret: %r", access_token.secret)
        self.assertTrue(True)


        


class CoreVerifyTest(GAETestBase):
    def setUp(self):
        init_recording()
        app = get_application()
        self.client = Client(app, BaseResponse)
        self.consumer_key = "e30e49d63907db14c48c5ad063ff7577b7ab5248"
        self.consumer_secret = "d06b6c54863ac33d12419dd04f7acb85c696f722"
        self.access_token = "c02b74809aaccf4972b9bb7059fa28aa91a255a3"
        self.access_token_secret = "9c676e003b8932ac49d4d3a18467c0b59e3e3fb6"

    def tearDown(self):
        disable_recording()


    def test_valid_request(self):
        """update the tokens in the setUp"""
        osg_auth = OSGOAuth(self.consumer_key, self.consumer_secret,
                self.access_token, self.access_token_secret)
        resp = osg_auth.request("http://localhost:8080/oauth/info", parameters={'friends': 'kates'}, raw_response=True)
        logging.debug(resp)
        
        self.assertTrue(True)

    def test_invalid_consumer_key(self):
        """client should raise error from provider"""
        osg_auth = OSGOAuth('asdfasd', 'asdfas93',
                self.access_token, self.access_token_secret)
        try:
            resp = osg_auth.request("http://localhost:8080/oauth/info", parameters={'friends': 'kates'}, raw_response=True)
            logging.debug(resp)
            self.assertTrue(False)
        except:
            self.assertTrue(True)
        
    def test_invalid_access_key(self):
        osg_auth = OSGOAuth(self.consumer_key, self.consumer_secret,
                'asdfas', 'asdfsd3')
        try:
            resp = osg_auth.request("http://localhost:8080/oauth/info", parameters={'friends': 'kates'}, raw_response=True)
            logging.debug(resp)
            self.assertTrue(False)
        except:
            self.assertTrue(True)

class CoreDeveloperTest(GAETestBase):
    
    def setUp(self):
        init_recording()
        app = get_application()
        self.client = Client(app, BaseResponse)

    def tearDown(self):
        disable_recording()

    def test_url_for(self):
        target_url = "/developer/app/4401"
        url = url_for("core/developer/app", app_id=4401)
        self.assertEquals(target_url, url)
