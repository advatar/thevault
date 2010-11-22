import os
import urllib
from operator import itemgetter
import simplejson as json
import oauth
from google_auth import PicasaWeb

from flask import Module, render_template, jsonify, g,\
        request, redirect, url_for, current_app,\
        send_file, abort, flash

from myvault.helpers import get_logger, get_pagination_params,\
        get_archive_file, Paginator, PhotoPaginator, stringify_unicode_keys,\
        is_online

from myvault.scheduler import reload_schedules
from picasaweb_app.helpers import run_backup
from picasaweb_app.forms import ScheduleForm
from settings import BACKUP_DIR, GOOGLE_OAUTH_CONSUMER_KEY,\
        GOOGLE_OAUTH_CONSUMER_SECRET
from myvault.api import get_settings, save_settings, get_paginated_archives,\
        get_archive, schedule_to_form_time, clear_archives

import gdata

module = Module(__name__, "picasaweb_app")

logger = get_logger()

@module.route('/')
def index():
    return render_template('picasaweb_app/index.html')

@module.route('/backup')
def backup():
    if not is_online():
        logger.debug('skipping picasaweb backup. we are offline')
        return jsonify({'error': 'offline'})

    logger.debug('running backup for picasaweb_app')

    preference = get_settings('picasaweb_app')

    def make_response(payload):
        response = app.make_response(jsonify(payload))
        response.headers['cache-control'] = 'no-cache'
        return response

    if not preference:
        logger.debug('no preference found.')
        return make_response({'error': 'no preference'})
    
    backup_time = run_backup(preference)
    logger.debug('done picasaweb backup')

    return jsonify({'backup_time': backup_time.strftime("%Y-%m-%d %H%M")})


@module.route('/setup')
def setup():
    return render_template('picasaweb_app/setup.html')

@module.route('/setup', methods=['POST'])
def do_setup():
    return redirect(url_for('preferences'))

@module.route('setup_link')
def setup_link():
    try:
        settings = get_settings('picasaweb_app')

        if settings:
            return render_template('picasaweb_app/manage_link.html')
        else:
            return render_template('picasaweb_app/setup_link.html')

    except Exception, e:
        logger.debug("error in setup_link view: %r", e)
        return ""

@module.route('/preferences')
def preferences():
    preference = get_settings('picasaweb_app')

    if not preference:
        logger.debug('no preference found. redirecting to setup')
        return redirect(url_for('setup'))

    schedule_form = ScheduleForm(prefix='schedule', **preference['schedule'])

    return render_template('picasaweb_app/preferences.html',
            schedule_form=schedule_form,
            profile=preference['profile'])

@module.route('/preferences', methods=['POST'])
def do_preferences():
    preference = get_settings('picasaweb_app')

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
   
    save_settings('picasaweb_app', preference)

    reload_schedules()
    flash('Picasaweb Settings updated.', 'info')
    return redirect(url_for('preferences'))

@module.route('/authorize')
def authorize():
    bridge = 'https://opensocialgraph.appspot.com/backup_bridge/google/authorize'
    local_url = url_for('register', _external=True)
    url = '%s?%s' % (bridge, urllib.urlencode({'redirect_url': local_url,
        'scope': 'https://picasaweb.google.com/data/'}),)
    return redirect(url)

@module.route('/register')
def register():
    access_token = request.values.get('access_token', None)
    logger.debug("picasa token: %r", access_token)
    if not access_token or access_token == "None":
        return render_template('picasaweb_app/register.html')
    token = oauth.OAuthToken.from_string(urllib.unquote(access_token))

    auth = PicasaWeb(GOOGLE_OAUTH_CONSUMER_KEY, GOOGLE_OAUTH_CONSUMER_SECRET,
            token.key, token.secret)

    try:
        profile = auth.get_profile()
    except Exception, e:
        logger.debug('authentication error: %r', e)
        flash('There was a problem authenticating you with Google. Please try again.', 'error')
        return render_template('picasaweb_app/register.html')

    access_token = {'access_token': token.key,
            'access_token_secret': token.secret}
    
    schedule = {
            'interval': 'daily',
            'timeofday': '0700'}

    schedule.update(schedule_to_form_time('0700'))

    save_settings('picasaweb_app',
            {'schedule': schedule,
                'tokens': access_token,
                'profile': profile})

    reload_schedules()
    return render_template('picasaweb_app/register.html')

@module.route('/archives')
def archives():
    page, per_page = get_pagination_params(request)
    profile = get_settings('picasaweb_app')

    if not profile:
        logger.debug('no profile found. picasaweb was not setup')
        return redirect(url_for('preferences'))

    archives = get_paginated_archives('picasaweb_app', page, per_page)

    return render_template('picasaweb_app/archives.html',
            archives=archives,
            profile=profile['profile'])


@module.route('/archives/<archive_id>/albums')
def archive_albums(archive_id):
    archive = get_archive('picasaweb_app', archive_id)
    data = get_archive_file('picasaweb_app', archive.filename)

    #logger.debug('%r', data['albums'])
    profile = get_settings('picasaweb_app')
    page, per_page = get_pagination_params(request, default_per_page=28)

    albums = Paginator(data['albums'], page=page, per_page=per_page)

    return render_template('picasaweb_app/albums.html',
            albums=albums,
            archive_id=archive.id,
            profile=profile['profile'])

@module.route('/archives/<archive_id>/albums/<album_id>')
def archive_album(archive_id, album_id):
    archive = get_archive('picasaweb_app', archive_id)
    data = get_archive_file('picasaweb_app', archive.filename)

    profile = get_settings('picasaweb_app')
    page, per_page = get_pagination_params(request, default_per_page=28)
    photos = sorted(data['albums'][album_id]['photos'].values(), key=itemgetter('published'), reverse=True)

    photos = Paginator(photos, page, per_page)

    return render_template('picasaweb_app/album.html',
            archive_id=archive_id,
            album_id=album_id,
            album=data['albums'][album_id],
            photos=photos,
            profile=profile['profile'])

@module.route('/archives/<archive_id>/albums/<album_id>/photos/<photo_id>')
def archive_album_photo(archive_id, album_id, photo_id):
    archive = get_archive('picasaweb_app', archive_id)
    data = get_archive_file('picasaweb_app', archive.filename)

    page, per_page = get_pagination_params(request, default_per_page=1)

    profile = get_settings('picasaweb_app')

    photos = sorted(data['albums'][album_id]['photos'].values(), key=itemgetter('published'), reverse=True)
    photos = PhotoPaginator(photos, photo_id)

    return render_template('picasaweb_app/photo.html',
            archive_id=archive_id,
            album_id=album_id,
            album=data['albums'][album_id],
            photos=photos,
            profile=profile['profile'])


@module.route('/image/album/photo/<album_id>_<photo_id>_<size>.jpg')
def album_photo_path(album_id, photo_id, size):
    image_file = os.path.join(
            BACKUP_DIR,
            'picasaweb_app',
            'albums',
            album_id,
            photo_id,
            '%s.jpg' % size)

    return send_file(image_file)

