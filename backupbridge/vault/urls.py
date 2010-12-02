# -*- coding: utf-8 -*-
# vault.urls
# 

# Following few lines is an example urlmapping with an older interface.
"""
from werkzeug.routing import EndpointPrefix, Rule

def make_rules():
  return [
    EndpointPrefix('vault/', [
      Rule('/', endpoint='index'),
    ]),
  ]

all_views = {
  'vault/index': 'vault.views.index',
}
"""

from kay.routing import (
  ViewGroup, Rule
)

view_groups = [
  ViewGroup(
    Rule('/', endpoint='index',
        view='vault.views.index'),
    Rule('/releases', endpoint='list_releases',
        view='vault.views.list_releases'),
    Rule('/releases/new', endpoint='new_release',
        view='vault.views.new_release'),
    Rule('/releases/create', endpoint='create_release',
        view='vault.views.create_release'),
    Rule('/releases/delete/<id>', endpoint='delete_release',
        view='vault.views.delete_release'),
    Rule('/releases/current', endpoint='current_release',
        view='vault.views.current_release'),
  )
]

