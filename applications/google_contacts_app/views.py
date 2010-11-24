# -*- coding: utf-8 -*-

import os
import urllib
import simplejson as json
import oauth
from google_auth import GoogleContacts

from flask import Module, render_template, jsonify, g,\
        request, redirect, url_for, current_app,\
        send_file, abort, flash
from myvault.helpers import get_logger, get_pagination_params,\
        get_archive_file, Paginator, PhotoPaginator, stringify_unicode_keys,\
        is_online
from myvault.scheduler import reload_schedules
from google_contacts_app.helpers import run_backup
from google_contacts_app.forms import ScheduleForm
from settings import BACKUP_DIR, GOOGLE_OAUTH_CONSUMER_KEY,\
        GOOGLE_OAUTH_CONSUMER_SECRET
from myvault.api import get_settings, save_settings, get_paginated_archives,\
        get_archive, schedule_to_form_time, clear_archives

import gdata

module = Module(__name__, "google_contacts_app")

logger = get_logger()

@module.route('/')
def index():
    return render_template('google_contacts_app/index.html')

@module.route('/backup')
def backup():
    if not is_online():
        logger.debug("skipping google contacts backup. we are offline")
        return jsonify({'error': 'offline'})

    logger.debug("running backup for google_contacts_app")

    preference = get_settings("google_contacts_app")

    def make_response(payload):
        response = app.make_response(jsonify(payload))
        response.headers['cache-control'] = 'no-cache'
        return response

    if not preference:
        logger.debug('no preference found.')
        return make_response({'error': 'no preference'})

    backup_time = run_backup(preference)
    logger.debug('done google_contacts backup')

    return jsonify({'backup_time': backup_time.strftime("%Y-%m-%d %H%M")})

@module.route('/setup')
def setup():
    return render_template('google_contacts_app/setup.html')

@module.route('/setup', methods=['POST'])
def do_setup():
    return redirect(url_for('preferences'))

@module.route('/setup_link')
def setup_link():
    try:
        settings = get_settings('google_contacts_app')

        if settings:
            return render_template('google_contacts_app/manage_link.html')
        else:
            return render_template('google_contacts_app/setup_link.html')
    except Exception, e:
        logger.debug('%r', e)
        return ""

@module.route('/preferences')
def preferences():
    preference = get_settings('google_contacts_app')

    if not preference:
        logger.debug('no preference found. redirecting to setup')
        return redirect(url_for('setup'))

    schedule_form = ScheduleForm(prefix='schedule', **preference['schedule'])
    #settings_form = SettingsForm(prefix='settings', **preference['settings'])

    return render_template('google_contacts_app/preferences.html',
            schedule_form=schedule_form,
            profile=preference['profile'])

@module.route('/preferences', methods=['POST'])
def do_preferences():
    preference = get_settings('google_contacts_app')

    if not preference:
        logger.debug('no preference found. redirecting to setup')
        return redirect(url_for('setup'))

    schedule_form = ScheduleForm(request.form, prefix='schedule')
    
    preference['schedule'] = {
        'interval': schedule_form.interval.data,
        'dayofmonth': schedule_form.dayofmonth.data,
        'dayofweek': schedule_form.dayofweek.data,
        'timeofday': schedule_form.timeofday.data,
        'hourofday': schedule_form.hourofday.data,
        'minuteofhour': schedule_form.minuteofhour.data,
        'ampm': schedule_form.ampm.data}
    save_settings('google_contacts_app', preference)

    reload_schedules()
    flash("Google Contacts settings updated.")
    return redirect(url_for("preferences"))

@module.route("/authorize")
def authorize():
    bridge = "https://opensocialgraph.appspot.com/backup_bridge/google/authorize"
    local_url = url_for("register", _external=True)
    url = "%s?%s" % (bridge, urllib.urlencode({'redirect_url': local_url, 'scope': 'https://www.google.com/m8/feeds/'}))
    return redirect(url)

@module.route("/register")
def register():
    access_token = request.values.get("access_token", None)
    if not access_token or access_token == "None":
        return render_template("google_contacts_app/register.html")
    token = oauth.OAuthToken.from_string(urllib.unquote(access_token))

    auth = GoogleContacts(GOOGLE_OAUTH_CONSUMER_KEY, GOOGLE_OAUTH_CONSUMER_SECRET,
            str(token.key), str(token.secret))
    try:
        profile = auth.get_profile()
    except Exception, e:
        logger.debug("authentication error: %r", e)
        flash("There was a problem authenticating you with Google. Please try again.", "error")
        return render_template("google_contacts_app/register.html")

    access_token = {'access_token': token.key,
            'access_token_secret': token.secret}

    schedule = {
            'interval': 'daily',
            'timeofday': '0700'}

    schedule.update(schedule_to_form_time('0700'))
    
    save_settings('google_contacts_app',
            {'schedule': schedule,
                'tokens': access_token,
                'profile': profile})

    reload_schedules()
    return render_template("google_contacts_app/register.html")
    

@module.route("/archives")
def archives():
    page, per_page = get_pagination_params(request)
    profile = get_settings("google_contacts_app")

    if not profile:
        logger.debug("no profile found. google_contacts_app was not setup")
        return redirect(url_for('preferences'))

    archives = get_paginated_archives("google_contacts_app", page, per_page)

    return render_template("google_contacts_app/archives.html",
            archives=archives,
            profile=profile['profile'])

@module.route("/archive/<archive_id>")
def archive(archive_id):
    archive = get_archive('google_contacts_app', archive_id)
    atom_data = get_archive_file("google_contacts_app", archive.filename)

    data = gdata.contacts.ContactsFeedFromString(atom_data.ToString())

    profile = get_settings("google_contacts_app")
    page, per_page = get_pagination_params(request)

    contacts = Paginator(data.entry, page=page, per_page=per_page)

    return render_template("google_contacts_app/archive.html",
            contacts=contacts,
            archive_id=archive_id,
            profile=profile['profile'])

# vim: set et sts=4 ts=4 sw=4
