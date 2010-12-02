# -*- coding: utf-8 -*-
# backup_bridge.urls
# 

# Following few lines is an example urlmapping with an older interface.
"""
from werkzeug.routing import EndpointPrefix, Rule

def make_rules():
  return [
    EndpointPrefix('backup_bridge/', [
      Rule('/', endpoint='index'),
    ]),
  ]

all_views = {
  'backup_bridge/index': 'backup_bridge.views.index',
}
"""

from kay.routing import (
  ViewGroup, Rule
)

view_groups = [
  ViewGroup(
    Rule('/', endpoint='index',
        view='backup_bridge.views.index'),
    Rule('/facebook/authorize', endpoint='facebook_authorize',
        view='backup_bridge.views.facebook_authorize'),
    Rule('/facebook/oauth_callback', endpoint='facebook_oauth_callback',
        view='backup_bridge.views.facebook_oauth_callback'),
    Rule('/facebook/register', endpoint='facebook_register',
        view='backup_bridge.views.facebook_register'),
    Rule('/google/authorize', endpoint='google_app_authorize',
        view='backup_bridge.views.google_app_authorize'),
    Rule('/google/oauth_callback', endpoint='google_app_oauth_callback',
        view='backup_bridge.views.google_app_oauth_callback'),
  )
]

