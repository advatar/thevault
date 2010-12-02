# -*- coding: utf-8 -*-
# core.urls
# 

# Following few lines is an example urlmapping with an older interface.
"""
from werkzeug.routing import EndpointPrefix, Rule

def make_rules():
  return [
    EndpointPrefix('core/', [
      Rule('/', endpoint='index'),
    ]),
  ]

all_views = {
  'core/index': 'core.views.index',
}
"""

from kay.routing import (
  ViewGroup, Rule
)

view_groups = [
  ViewGroup(
    Rule('/', endpoint='index',
        view='core.views.index'),

    # developer
    """
    Rule('/developer/app/<int:app_id>', endpoint='developer/app',
        view='core.views.developer_app'),
    Rule('/developer/apps', endpoint='developer/apps',
        view='core.views.developer_apps'),
    Rule('/developer/register', endpoint='developer/register',
        view='core.views.developer_register'),
    Rule('/developer/do_register', endpoint='developer/do_register',
        view='core.views.developer_do_register'),
    """
    # oauth
    """
    Rule('/oauth/request_token', endpoint='oauth/request_token',
        view='core.views.oauth_request_token'),
    Rule('/oauth/access_token', endpoint='oauth/access_token',
        view='core.views.oauth_access_token'),
    Rule('/oauth/authorize', endpoint='oauth/authorize',
        view='core.views.oauth_authorize'),
    Rule('/oauth/authorized', endpoint='oauth/authorized',
        view='core.views.oauth_authorized'),
    Rule('/oauth/test_request_token', endpoint='oauth/test_request_token',
        view='core.views.test_request_token'),
    Rule('/oauth/info', endpoint='oauth/info',
        view='core.views.oauth_info'),
    """
  )
]

