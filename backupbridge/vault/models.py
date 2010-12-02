# -*- coding: utf-8 -*-
# vault.models

from google.appengine.ext import db

# Create your models here.

class Vault(db.Model):
    version = db.StringProperty(required=True)
    created_at = db.DateTimeProperty(auto_now_add=True)

