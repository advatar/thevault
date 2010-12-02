# -*- coding: utf-8 -*-
# osg.urls
# 

# Following few lines is an example urlmapping with an older interface.
"""
from werkzeug.routing import EndpointPrefix, Rule

def make_rules():
  return [
    EndpointPrefix('osg/', [
      Rule('/', endpoint='index'),
    ]),
  ]

all_views = {
  'osg/index': 'osg.views.index',
}
"""

from kay.routing import (
  ViewGroup, Rule
)

view_groups = [
  ViewGroup(
    Rule('/', endpoint='index',
        view='osg_app.views.index'),
    Rule('/dashboard', endpoint='dashboard',
        view='osg_app.views.dashboard'),
  )
]

