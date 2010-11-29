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
from distutils import dir_util
from ConfigParser import ConfigParser
import simplejson as json
import time, datetime
from flask import url_for, jsonify, render_template, current_app, g,\
        send_file, request
from jinja2 import evalcontextfilter, Markup, escape
from werkzeug import import_string
from myvault.helpers import get_logger, utc_to_local, stringify_unicode_keys,\
        backup_is_on_schedule, is_online
from myvault.scheduler import add_schedule
from myvault.models import db, Archive, BackupProgress, UserPreference, AppMessage
from myvault.api import get_backup_progress, get_settings, get_recent_archive, \
        save_settings, run_at_startup
from myvault.forms import AppSettingsForm
from settings import HOST, PORT, KRON, BACKUP_DIR, CONFIG_DIR

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

logger = get_logger()

def default_views(app):

    def make_response(payload):
        """
        Creates a no-cache response. Handy for AJAX calls.
        """
        response = app.make_response(payload)
        response.headers['cache-control'] = 'no-cache'
        return response

    @app.context_processor
    def enabled_services():
        """
        Returns a list of services enabled.
        """
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
        """
        Convert \n to <br>
        """
        result = u'\n\n'.join(u'%s' % p.replace('\n', '<br>\n') \
                for p in _paragraph_re.split(value))
        if eval_ctx.autoescape:
            result = Markup(result)
        return result

    @app.route("/")
    def index():
        preference = get_settings('global')
        backup_dir = preference.get('backup_dir', BACKUP_DIR)
        return render_template("index.html", backup_dir=backup_dir)

    @app.route("/load_schedules")
    def load_schedules():
        """
        Load schedules from db to kronos scheduler.
        Starts the backup routine for an app module if we missed a schedule.
        """
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
                return make_response("schedule loaded")

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

        return make_response("schedule loaded")


    @app.route("/reload_schedules")
    def reload_schedules():
        """
        Reload all schedules
        """
        logger.debug("in reload schedules")        
        modules = app.modules

        def load_sked():
            try:
                url = "http://%s:%s/load_schedules" % (HOST, PORT,)
                urllib2.urlopen(url, timeout=1)
            except Exception, e:
                pass
        
        KRON.add_single_task(load_sked, 'load_sked', 3, 'threaded', None, None)

        return make_response("rescheduled")

    @app.route("/connection_status")
    def connection_status():
        """
        Returns internet connection status.
        """
        status = 'offline'
        if is_online():
            status = 'online'
        
        return make_response(jsonify({'status': status}))
    
    @app.route('/update_status')
    def update_status():
        status = 'outdated'

        return make_response(jsonify({'status': status}))

    @app.route("/dashboard")
    def dashboard():
        return "app dashboard"

    @app.route("/backup_progress/<app_name>")
    def backup_progress(app_name):
        """
        Return from db the progress of the backup routine.
        """
        progress = get_backup_progress(app_name)

        if progress:
            if not progress.ended_at:
                return make_response(jsonify({'status': True, 'progress': progress.progress}))

        return make_response(jsonify({'status': False, 'progress': 0}))

    @app.route('/settings')
    def app_settings():
        """
        Show the application settings page.
        """
        preference = get_settings('global')
        if not preference.has_key('backup_dir') or not preference['backup_dir']:
            preference['backup_dir'] = BACKUP_DIR
        form = AppSettingsForm(**preference)
        return render_template('settings.html', form=form)

    @app.route('/settings', methods=['POST'])
    def do_app_settings():
        """
        Update application settings
        """
        from flask import request, flash, redirect

        preference = get_settings('global')
        new_preference = AppSettingsForm(request.form)
        preference['run_at_startup'] = new_preference.run_at_startup.data
        
        backup_dir = new_preference.backup_dir.data

        home_dir = get_home_dir()
        logger.debug("home dir is: %r", home_dir)
        logger.debug("backup dir is: %r", backup_dir)
        if not backup_dir.startswith(home_dir):
            flash("Invalid Backup Directory path", "error")
            return redirect(url_for('.app_settings'))

        preference['backup_dir'] = backup_dir
        
        need_restart = False
        if not is_same_path(BACKUP_DIR, backup_dir):
            move_backup_dir(backup_dir)
            need_restart = True

        save_settings('global', preference)
        run_at_startup(preference['run_at_startup'])
        save_config('backup_dir', backup_dir)
        flash('Application settings updated!')
        if need_restart:
            return redirect(url_for('.restarting'))
        return redirect(url_for('.app_settings'))

    @app.route('/restarting')
    def restarting():
        """
        Show a restarting page while waiting for the server to restart.
        """
        return render_template('restarting.html')


    def save_config(name, value):
        """
        Update the config file mycubevault.cfg.
        Server restart needed see new values.
        """
        config_parser = ConfigParser()
        config_path = os.path.join(CONFIG_DIR, "mycubevault.cfg")
        try:
            config_parser.readfp(open(config_path))
        except IOError, e:
            pass

        section = 'MyCube Vault'
        if not config_parser.has_section(section):
            config_parser.add_section(section)

        config_parser.set(section, name, value)
        config_parser.write(open(config_path, "wb"))


    def move_backup_dir(path):
        """
        Copy the backup dir to a given path. Removes the old path.
        """
        dir_util.copy_tree(BACKUP_DIR, path)
        dir_util.remove_tree(BACKUP_DIR)

    def get_dirs(path):
        """
        Return the a list of directories found in path.
        """
        return [os.path.realpath(os.path.join(path,d)) for d in os.listdir(path) if os.path.isdir("%s/%s" % (path, d,))]

    def get_home_dir():
        """
        Get user's home dir.
        """
        if os.environ.has_key('HOME'):
            return os.path.realpath(os.environ['HOME'])
        elif os.environ.has_key('HOMEPATH'):
            return os.path.realpath(os.environ['HOMEPATH'])
        else:
            return os.path.realpath(os.path.expanduser('~'))

    def is_same_path(path1, path2):
        """
        Compare two paths ignoring trailing space and /.
        """
        path1 = path1.split(os.path.sep)
        path2 = path2.split(os.path.sep)

        return "".join(path1).strip() == "".join(path2).strip()

    @app.route('/backup_dir_suggest')
    def backup_dir_suggest():
        """
        Returns a list of path suggestions based on the prefix submitted.
        """
        term = request.values.get('term', None)
        splits = term.split(os.path.sep)
        path = os.path.sep.join(splits[:-1])
        selected = splits[-1:]
        home_dir = get_home_dir()

        # for now limit user in their home dir
        # assume we are in installed mode deal with USBMODE later.
        if not path.startswith(home_dir):
            dirs = get_dirs(home_dir)
            search_term = home_dir
        else:
            dirs = get_dirs(path)
            search_term = term

        dirs.sort()
        paths = [{'id': d, 'label': d, 'value': d} for d in dirs if d.startswith(str(search_term))]
        return make_response(json.dumps(paths))

    @app.route("/check_restart")
    def check_restart():
        """
        Check if there's a server restart job pending.
        Used by the launcher.
        """
        logger.debug("in check_restart")
        app_message = AppMessage.query and \
                AppMessage.query\
                    .filter_by(topic='server_restart')\
                    .order_by('id ASC')\
                    .first()

        res = "false"
        if app_message:
            res = "true"
            db.session.delete(app_message)
            db.session.commit()
        return make_response(res)

# vim: set sts=4 sw=4 ts=4:
