# -*- coding: utf-8 -*-
# core.models

import hashlib
import random


from google.appengine.ext import db

from kay.auth.models import DatastoreUser
from gaelibs.oauth import OAuthToken, OAuthConsumer, OAuthError

from gaelibs.decorators import log_wrapper
# Create your models here.

import logging

class User(DatastoreUser):
    pass
    
class ConsumerApp(db.Model):
    user = db.ReferenceProperty(User)
    consumer_key = db.StringProperty(required=True)
    consumer_secret = db.StringProperty(required=True)
    application_name = db.StringProperty(required=True)
    callback_url = db.StringProperty(required=True)
    created_at = db.DateTimeProperty(auto_now_add=True)
    updated_at = db.DateTimeProperty(auto_now=True)

class RequestToken(db.Model):
    user = db.ReferenceProperty(User)
    consumer = db.ReferenceProperty(ConsumerApp)
    token_key = db.StringProperty(required=True)
    token_secret = db.StringProperty(required=True)
    nonce = db.StringProperty()
    verifier = db.StringProperty()
    created_at = db.DateTimeProperty(auto_now_add=True)
    updated_at = db.DateTimeProperty(auto_now=True)

class AccessToken(RequestToken):
    pass

class Nonce(db.Model):
    consumer_key = db.StringProperty(required=True)
    token_key = db.StringProperty(required=True)
    nonce = db.StringProperty(required=True)

class OAuthDataStore(object):
    """A database abstraction used to lookup consumers and tokens."""

    def lookup_consumer(self, key):
        """-> OAuthConsumer."""
        consumer = ConsumerApp.all().filter("consumer_key =", key).get()
        if consumer:
            oauth_consumer = OAuthConsumer(consumer.consumer_key, consumer.consumer_secret)
            return oauth_consumer
        return None

    def lookup_token(self, token_type, token_token):
        """-> OAuthToken."""
        if token_type == "request":
            query = RequestToken.all()
        elif token_type == "access":
            query = AccessToken.all()
        token = query.filter("token_key =", token_token).get()
        if token:
            return OAuthToken(token.token_key, token.token_secret)
        return None
        
    def lookup_nonce(self, oauth_consumer, oauth_token, nonce):
        """-> OAuthToken."""
        #raise NotImplementedError
        if not oauth_token:
            return oauth_token

        query = Nonce.all()
        query.filter("consumer_key =", oauth_consumer.key)
        query.filter("token_key =", oauth_token.key)
        query.filter("nonce =", nonce)
        used_nonce = query.get()

        if used_nonce:
            return oauth_token

        use_nonce = Nonce(consumer_key=oauth_consumer.key,
                token_key=oauth_token.key,
                nonce=nonce)
        use_nonce.put()
        return None

    def fetch_request_token(self, oauth_consumer, oauth_callback):
        """
        Should generate a fresh set of tokens everytime.
        returns OAuthToken
        """
        token = self.generate_tokens()
        consumer = ConsumerApp.all().filter("consumer_key =", oauth_consumer.key).get()
        
        request_token = RequestToken(consumer=consumer,
                callback_url=oauth_callback,
                token_key=token.key,
                token_secret=token.secret)
        request_token.put()
        return token

    @staticmethod
    def generate_tokens():
        k = hashlib.sha1(str(random.getrandbits(10))).hexdigest()
        v = hashlib.sha1(str(random.getrandbits(10))).hexdigest()
        return OAuthToken(k, v)

    def fetch_access_token(self, oauth_consumer, oauth_token, oauth_verifier):
        """
        If consumer already have user's access permission, return old
        access_token else return a new one.
        returns OAuthToken
        """
        query = RequestToken.all()
        query.filter("token_key =", oauth_token.key)
        query.filter("verifier =", oauth_verifier)
        request_token = query.get()

        query = AccessToken.all()
        query.filter("consumer =", request_token.consumer.key())
        query.filter("user =", request_token.user.key())
        access_token = query.get()

        if access_token:
            return OAuthToken(access_token.token_key,
                    access_token.token_secret)

        token = self.generate_tokens()
        access_token = AccessToken(token_key=token.key,
                token_secret=token.secret,
                consumer=request_token.consumer,
                user = request_token.user,
                verifier=request_token.verifier)
        access_token.put()
        return token

    def authorize_request_token(self, oauth_token, user):
        """-> OAuthToken."""
        query = RequestToken.all().filter("token_key =", oauth_token.key)
        request_token = query.get()
        if request_token:
            request_token.user = user
            request_token.put()
            return oauth_token
        raise OAuthError('Invalid request token')

