# -*- coding: utf-8 -*-

"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""

import os
import urllib
from operator import itemgetter
import simplejson as json
import facebook
from flask import Module, render_template, jsonify, g,\
        request, redirect, url_for, current_app,\
        send_file, abort, flash
from myvault.helpers import get_logger, get_pagination_params,\
        get_archive_file, Paginator, PhotoPaginator, stringify_unicode_keys,\
        is_online
from myvault.scheduler import reload_schedules
from .forms import ScheduleForm, SettingsForm
from .helpers import run_backup
from settings import BACKUP_DIR, BRIDGE
from myvault.api import get_settings, save_settings, get_paginated_archives,\
        get_archive, schedule_to_form_time, clear_archives


module = Module(__name__, "facebook_app")

logger = get_logger()

@module.route("/")
def index():
    return render_template("facebook_app/index.html")


@module.route("/backup")
def backup():
    if not is_online():
        logger.debug("skipping backup. we are offline")
        return jsonify({'error': 'offline'})

    logger.debug("running backup for facebook_app")

    preference = get_settings("facebook_app")

    logger.debug("%r", preference) 

    def make_response(payload):
        response = app.make_response(jsonify(payload))
        response.headers['cache-control'] = 'no-cache'
        return response

    if not preference:
        logger.debug('no preference found.')
        return jsonify({'error': 'no preference'})

    backup_time = run_backup(preference)

    return jsonify({'backup_time': backup_time.strftime("%Y-%m-%d %H%M")})

@module.route("/setup")
def setup():
    return render_template("facebook_app/setup.html")


@module.route("/setup", methods=["POST"])
def do_setup():
    return redirect(url_for("preferences"))

@module.route("/setup_link")
def setup_link():
    try:
        settings = get_settings('facebook_app')

        if settings:
            return render_template("facebook_app/manage_link.html")
        else:
            return render_template("facebook_app/setup_link.html")
    except Exception, e:
        logger.debug("%r", e)

@module.route("/preferences")
def preferences():

    preference = get_settings("facebook_app")

    if not preference:
        logger.debug('no preference found. redirecting to setup')
        return redirect(url_for("setup"))

    schedule_form = ScheduleForm(prefix="schedule", **preference['schedule'])
    settings_form = SettingsForm(prefix="settings", **preference['settings'])

    return render_template("facebook_app/preferences.html",
            schedule_form=schedule_form,
            settings_form=settings_form,
            profile=preference['profile'])


@module.route("/preferences", methods=['POST'])
def do_preferences():
    preference = get_settings("facebook_app")

    if not preference:
        logger.debug('no preference found. redirecting to setup')
        return redirect(url_for('setup'))

    schedule_form = ScheduleForm(request.form, prefix='schedule')
    settings_form = SettingsForm(request.form, prefix='settings')

    preference['settings'] = {
        'statuses': settings_form.statuses.data,
        'events': settings_form.events.data,
        'albums': settings_form.albums.data,
        'notes': settings_form.notes.data,
        'links': settings_form.links.data,
        'friends': settings_form.friends.data,
        'photos': settings_form.photos.data}

    preference['schedule'] = {
        'interval': schedule_form.interval.data,
        'dayofmonth': schedule_form.dayofmonth.data,
        'dayofweek': schedule_form.dayofweek.data,
        'timeofday': schedule_form.timeofday.data,
        'hourofday': schedule_form.hourofday.data,
        'minuteofhour': schedule_form.minuteofhour.data,
        'ampm': schedule_form.ampm.data}

    save_settings("facebook_app", preference)
    reload_schedules() 
    flash("Facebook settings updated.")
    return redirect(url_for("preferences"))


@module.route("/archives")
def archives():
    page, per_page = get_pagination_params(request) 
    profile = get_settings("facebook_app")

    if not profile:
        logger.debug('no archive found. facebook_app is not set up')
        return redirect(url_for("preferences"))
    
    archives = get_paginated_archives("facebook_app", page, per_page)

    return render_template("facebook_app/archives.html",
            archives=archives,
            profile=profile['profile'])


@module.route("/archives/<archive_id>")
@module.route("/archives/<archive_id>/<item>")
def archive(archive_id, item=None):
    if item is None:
        return abort(404)
    archive = get_archive('facebook_app', archive_id)

    data = get_archive_file("facebook_app", archive.filename)

    reverse = True
    sort_key = "id"

    if item == "albums":
        albums = [album for k, album in data['albums'].iteritems() if len(album['photos']) > 0]
        data['albums'] = albums
        sort_key = "created_time"
    elif item == "friends":
        sort_key = "name"
        reverse = False
    elif item == "statuses":
        sort_key = "updated_time"
    elif item == "events":
        sort_key = "start_time"
    elif item == "photos":
        sort_key = "created_time"

    try:
        requested_data = sorted(data[str(item)], key=itemgetter(sort_key), reverse=reverse)
    except KeyError, e:
        requested_data = {}

    profile = get_settings("facebook_app")
    page, per_page = get_pagination_params(request)
    if item == "albums":
        per_page = 28
    return render_template("facebook_app/%s.html" % item,
            **{str(item): Paginator(requested_data, page, per_page),
                "archive_id": archive_id,
                "profile": profile['profile']})


@module.route("/archives/<archive_id>/albums/<album_id>/photos")
def archive_album(archive_id, album_id):
    archive = get_archive('facebook_app', archive_id)
    data = get_archive_file("facebook_app", archive.filename)

    page, per_page = get_pagination_params(request, default_per_page=28)
    photos = sorted(data['albums'][album_id]['photos'].values(), key=itemgetter('created_time'), reverse=True)
    photos = Paginator(photos, page, per_page)

    preference = get_settings('facebook_app')

    return render_template("facebook_app/album_photos.html",
            archive_id=archive_id,
            album_id=album_id,
            album=data['albums'][album_id],
            photos=photos,
            profile=preference['profile'])


@module.route("/archives/<archive_id>/albums/<album_id>/photos/<photo_id>")
def archive_album_photo(archive_id, album_id, photo_id):
    archive = get_archive('facebook_app', archive_id)
    data = get_archive_file("facebook_app", archive.filename)

    page, per_page = get_pagination_params(request, default_per_page=1)
    
    preference = get_settings('facebook_app')
    photos = sorted(data['albums'][album_id]['photos'].values(), key=itemgetter('created_time'), reverse=True)
    photos = PhotoPaginator(photos, photo_id)

    return render_template("facebook_app/album_photo.html",
            archive_id=archive_id,
            album_id=album_id,
            album=data['albums'][album_id],
            photos=photos,
            profile=preference['profile'])


@module.route("/archives/<archive_id>/photos/<photo_id>")
def archive_photo(archive_id, photo_id):
    archive = get_archive('facebook_app', archive_id)
    data = get_archive_file('facebook_app', archive.filename)

    page, per_page = get_pagination_params(request, default_per_page=1)

    preference = get_settings('facebook_app')

    photos = sorted(data['photos'], key=itemgetter('created_time'), reverse=True)
    photos = PhotoPaginator(photos, photo_id)

    return render_template('facebook_app/photo.html',
            archive_id=archive_id,
            photos=photos,
            profile=preference['profile'])


@module.route("/schedule")
def schedule():
    preference = get_settings('facebook_app') 
    if preference:
        return jsonify(preference.schedule)
    return jsonify({})


@module.route("/schedules")
def schedules():
    preferences = get_all_settings('facebook_app')

    skeds = {}
    for preference in preferences:
        skeds[preference['user_id']] = preference['schedule']

    if skeds:
        return jsonify(skeds)
    return jsonify({})


@module.route("/authorize")
def authorize():
    #bridge = "https://opensocialgraph.appspot.com/backup_bridge/facebook/authorize"
    bridge = BRIDGE
    logger.debug("brige is %r", bridge)
    #bridge = "http://mycubeci.redsector.com.sg/bridge/v1/socialNetworkBridge/authenticate1"
    local_url = url_for("register", _external=True)
    url = "%s?%s" % (bridge, urllib.urlencode({'redirect_url': local_url}))
    print "%r" % url
    return redirect(url)


@module.route("/register")
def register():
    access_token = request.values.get("access_token", None)
    if not access_token or access_token == "None":
        return render_template("facebook_app/register.html")
    try:
        graph = facebook.GraphAPI(access_token)
        profile = graph.get_object('me')
        settings = {
                'events': True,
                'friends': True,
                'notes': True,
                'albums': True,
                'links': True,
                'statuses': True,
                'photos': True}

        schedule = {
                'interval': 'daily',
                'timeofday': '0700'}
        schedule.update(schedule_to_form_time('0700'))

        save_settings("facebook_app",
                {'settings': settings,
                    'schedule': schedule,
                    'tokens': access_token,
                    'profile': profile})

        reload_schedules()

        return render_template("facebook_app/register.html")
    except Exception, e:
        logger.debug("%r", e)


@module.route("/images/profile/<image_file>")
def profile_pics_path(image_file):
    image_file = os.path.join(
            BACKUP_DIR,
            'facebook_app',
            'profile_pics',
            image_file)

    return send_file(image_file)

@module.route("/images/album/photo/<album_id>_<photo_id>_<size>.jpg")
def album_photo_path(album_id, photo_id, size):
    image_file = os.path.join(
            BACKUP_DIR,
            'facebook_app',
            'albums',
            album_id,
            photo_id,
            "%s.jpg" % size)

    return send_file(image_file)

@module.route("/images/photo/<photo_id>_<size>.jpg")
def photo_path(photo_id, size):
    image_file = os.path.join(
            BACKUP_DIR,
            'facebook_app',
            'photos',
            photo_id,
            "%s.jpg" % size)

    return send_file(image_file)

