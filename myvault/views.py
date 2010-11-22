"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""

import os
import time
import urllib2
import re
import simplejson as json
import time, datetime
from flask import url_for, jsonify, render_template, current_app, g,\
        send_file
from jinja2 import evalcontextfilter, Markup, escape
from werkzeug import import_string
from myvault.helpers import get_logger, utc_to_local, stringify_unicode_keys,\
        backup_is_on_schedule, is_online
from myvault.scheduler import add_schedule
from myvault.models import db, Archive, BackupProgress
from myvault.api import get_backup_progress, get_settings, get_recent_archive
from settings import HOST, PORT, KRON

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

logger = get_logger()

def default_views(app):

    @app.context_processor
    def enabled_services():
        modules = app.modules
        services = {}

        for app_name, _ in modules.iteritems():
            if app_name in ['base', 'account']:
                continue
            module = import_string(app_name)
            services[app_name] = {
                    'title': module.APP_TITLE,
                    'name': app_name}

        return dict(enabled_services=services)


    @app.template_filter('strftime')
    def custom_strftime(t, format):
        return time.strftime(format, t)


    @app.template_filter('strptime')
    def custom_strptime(t, format):
        return time.strptime(t, format)

    @app.template_filter('hasattr')
    def custom_hasattr(obj, att):
        return hasattr(obj, att)

    @app.template_filter('utc_to_local')
    def utc_to_local_filter(t):
        return utc_to_local(t)


    @app.template_filter()
    @evalcontextfilter
    def nl2br(eval_ctx, value):
        result = u'\n\n'.join(u'%s' % p.replace('\n', '<br>\n') \
                for p in _paragraph_re.split(value))
        if eval_ctx.autoescape:
            result = Markup(result)
        return result

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/load_schedules")
    def load_schedules():
        logger.debug("in load_schedules")
        modules = app.modules

        for app_name in modules.keys():
            if app_name in ['base', 'account']:
                continue
            logger.debug("loading schedule for %s", app_name)
            
            settings = get_settings(app_name)
            if not settings:
                continue

            logger.debug("%r", settings['schedule'])
            def callback(app_name):
                try:
                    url = "http://%s:%s/%s/backup" % (HOST, PORT, app_name)
                    progress = get_backup_progress(app_name)
                    
                    if not progress:
                        urllib2.urlopen(url).read()
                except Exception, e:
                    logger.debug("%r", e)

            taskname = "%s" % (app_name)

            add_schedule(taskname, settings['schedule'], callback)
            logger.debug("schedule added")
            today = datetime.datetime.today()

            if not is_online():
                logger.debug("we are offline. skipping backup on boot")
                return "schedule loaded"

            archive = get_recent_archive(app_name) 
            if archive:
                logger.debug('there is an archive')
                try:
                    if not backup_is_on_schedule(
                            today,
                            archive.archived_at,
                            settings['schedule']):
                        logger.debug("we missed a backup schedule. starting backup")
                        KRON.add_single_task(callback, 'backup_%s' % app_name,
                                1, 'threaded', [app_name], None)
                    else:
                        logger.debug('we are on schedule')
                except Exception, e:
                    logger.debug('error: %r' % e)
            else:
                logger.debug("no backup found. starting backup")
                KRON.add_single_task(callback, 'backup_%s' % app_name, 1, 'threaded', [app_name], None)

        return "schedule loaded"


    @app.route("/reload_schedules")
    def reload_schedules():
        logger.debug("in reload schedules")        
        modules = app.modules

        def load_sked():
            try:
                url = "http://%s:%s/load_schedules" % (HOST, PORT,)
                urllib2.urlopen(url, timeout=1)
            except Exception, e:
                pass
        
        KRON.add_single_task(load_sked, 'load_sked', 3, 'threaded', None, None)

        return "rescheduled"

    @app.route("/connection_status")
    def connection_status():
        def make_response(payload):
            response = app.make_response(payload)
            response.headers['cache-control'] = 'no-cache'
            return response

        status = 'offline'
        if is_online():
            status = 'online'
        
        return make_response(jsonify({'status': status}))
    
    @app.route('/update_status')
    def update_status():
        def make_response(payload):
            response = app.make_response(payload)
            response.headers['cache-control'] = 'no-cache'
            return response
        status = 'outdated'

        return make_response(jsonify({'status': status}))

    @app.route("/dashboard")
    def dashboard():
        return "app dashboard"

    @app.route("/backup_progress/<app_name>")
    def backup_progress(app_name):
        def make_response(payload):
            response = app.make_response(jsonify(payload))
            response.headers['cache-control'] = 'no-cache'
            return response

        progress = get_backup_progress(app_name)

        if progress:
            if not progress.ended_at:
                return make_response({'status': True, 'progress': progress.progress})

        return make_response({'status': False, 'progress': 0})

