# -*- coding: utf-8 -*-
"""
vault.views
"""

"""
import logging

from google.appengine.api import users
from google.appengine.api import memcache
from werkzeug import (
  unescape, redirect, Response,
)
from werkzeug.exceptions import (
  NotFound, MethodNotAllowed, BadRequest
)

from kay.utils import (
  render_to_response, reverse,
  get_by_key_name_or_404, get_by_id_or_404,
  to_utc, to_local_timezone, url_for, raise_on_dev
)
from kay.i18n import gettext as _
from kay.auth.decorators import login_required

"""

from werkzeug import redirect, Response
from kay.utils import render_to_response, url_for
from kay.auth.decorators import admin_required
from gaelibs.decorators import restrict_to_methods

from vault.models import Vault
from vault.forms import ReleaseForm
# Create your views here.

@admin_required
def index(request):
    return render_to_response('vault/index.html', {'message': 'Hello'})

@admin_required
def list_releases(request):
    releases = Vault.all().order('-version').fetch(10)
    return render_to_response('vault/list_releases.html', 
            {'releases': releases})

@admin_required
def new_release(request):
    form = ReleaseForm()
    return render_to_response('vault/new_release.html',
            {'form': form.as_widget()})

@restrict_to_methods('POST')
@admin_required
def create_release(request):
    form = ReleaseForm()
    if form.validate(request.form):
        form.save()
        return redirect(url_for('vault/list_releases'))
    return render_to_response('vault/new_release.html',
            {'form': form.as_widget()})

@restrict_to_methods('POST')
@admin_required
def delete_release(request, id):
    release = Vault.get(id)
    release.delete()
    return redirect(url_for('vault/list_releases'))

def current_release(request):
    release = Vault.all().order('-version').get()
    if release:
        return Response(release.version)
    else:
        return Response("0")

