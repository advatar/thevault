# -*- coding: utf-8 -*-
"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""

import os, sys
import urllib2
from flask import Flask
import cherrypy
from myvault.database import db
import myvault.models
from werkzeug import import_string
import logging, logging.handlers
import ConfigParser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
import kronos

VERSION = "0.1.2" # major.minor.patch
USBMODE = False

def get_path(target):
    path = os.path.dirname(os.path.realpath(__file__))
    if path.endswith('library.zip'):
        new_path = os.path.sep.join(path.split(os.path.sep)[:-1] + [target])
    else:
        new_path = os.path.sep.join(path.split(os.path.sep) + [target])
    return new_path

def config_defaults():
    defaults = {}

    defaults['HOST'] = "localhost.mycube.com"

    try:
        import socket
        host = socket.gethostbyaddr(defaults['HOST'])
    except Exception, e:
        defaults['HOST'] = '127.0.0.1'

    try:
        defaults['PORT'] = str(int(sys.argv[1]))
    except:
        defaults['PORT'] = "8000"

    defaults['APP_DIR'] = os.path.dirname(__file__)
    if sys.platform == "win32":
        import winhelpers
        folders = winhelpers.get_user_folders()
        defaults['APP_DIR'] = os.path.join(folders['AppData'], 'MyCube Vault')
        defaults['CONFIG_DIR'] = os.path.join(folders['AppData'], 'MyCube Vault')
        defaults['BACKUP_DIR'] = os.path.join(defaults['CONFIG_DIR'], 'data')
    elif sys.platform == 'darwin':
        defaults['CONFIG_DIR'] = "%s/Library/Application Support/MyCube Vault" % os.environ['HOME']
        defaults['BACKUP_DIR'] = os.path.join(defaults['CONFIG_DIR'], 'data')
        #APP_DIR = "%s/Library/Application Support/MyCube Vault" % os.environ['HOME']
        defaults['APP_DIR'] = os.getcwd()
    else:
        defaults['APP_DIR'] = os.path.dirname(os.path.realpath(__file__)) 
        defaults['CONFIG_DIR'] = os.path.join(os.path.expanduser('~'), '.mycube')
        defaults['BACKUP_DIR'] = os.path.join(defaults['CONFIG_DIR'], 'data')

    #BACKUP_DIR = os.getcwd()
    if USBMODE:
        defaults['APP_DIR'] = os.getcwd()
        defaults['CONFIG_DIR'] = os.path.join(defaults['APP_DIR'], os.path.pardir)
        defaults['BACKUP_DIR'] = os.path.join(defaults['CONFIG_DIR'], 'Data')

    defaults['GOOGLE_OAUTH_CONSUMER_KEY'] = "opensocialgraph.appspot.com"
    defaults['GOOGLE_OAUTH_CONSUMER_SECRET'] = "ZwKQP4ILJ5G6witkPvCz7Jzx"

    defaults['BRIDGE'] = "https://opensocialgraph.appspot.com/backup_bridge/facebook/authorize"
    return defaults


config_parser = ConfigParser.ConfigParser(config_defaults())

section = 'MyCube Vault'

if not config_parser.has_section(section):
    config_parser.add_section(section)

CONFIG_DIR = config_parser.get(section, 'config_dir')
CONFIG_FILE  = os.path.join(CONFIG_DIR, "mycubevault.cfg")

try:
    config_parser.readfp(open(CONFIG_FILE))
except:
    pass

HOST = config_parser.get(section, 'host')
PORT = config_parser.getint(section, 'port')
APP_DIR = config_parser.get(section, 'app_dir')
BACKUP_DIR = config_parser.get(section, 'backup_dir')

BRIDGE = config_parser.get(section, "bridge")
GOOGLE_OAUTH_CONSUMER_KEY = config_parser.get(section, 'google_oauth_consumer_key')
GOOGLE_OAUTH_CONSUMER_SECRET = config_parser.get(section, 'google_oauth_consumer_secret')
DEBUG = False
SECRET_KEY = "asdfasdfasfsadf"
SQLALCHEMY_DATABASE_URI = "sqlite:////%s/mc.db" % os.path.sep.join(CONFIG_DIR.split(os.path.sep)[1:])
SQLALCHEMY_ECHO = False
KRON = kronos.ThreadedScheduler()
KRON.tasks = {}

def create_app(config=None):
    app = Flask("myvaultapp")

    app.config.from_object(__name__)
    
    if config is not None:
        app.config.from_object(config)

    app_dir = app.config['APP_DIR']
    config_dir = app.config['CONFIG_DIR']
    backup_dir = app.config['BACKUP_DIR']
    try:
        os.makedirs(config_dir, mode=0766)
    except OSError, e:
        pass

    try:
        os.makedirs(backup_dir, mode=0766)
    except OSError, e:
        pass

    try:
        os.makedirs(app_dir, mode=0766)
    except OSError, e:
        pass

    for d in ["applications"]:
        path = os.path.join(app_dir, d)
        sys.path.insert(0,path)


    from myvault.scheduler import init_scheduler
    init_scheduler(app)

    logger = app.logger
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    rh = logging.handlers.RotatingFileHandler(os.path.join(config_dir, 'myvault.log'))
    rh.setLevel(logging.DEBUG)
    rh.setFormatter(formatter)

    del logger.handlers[:]
    logger.addHandler(rh)

    if app.config['DEBUG']:
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    db.init_app(app)
    if sys.platform == 'darwin':
        applications_path = os.path.join(app_dir,"applications")
    else:
        applications_path = get_path("applications") 

    sys.path.insert(0, applications_path)
    
    for name in os.listdir(applications_path):
        try:
            view = import_string("%s.views" % name)
            if name == "base":
                mount = ""
                app.register_module(view.module, url_prefix="/%s" % mount)
            app.register_module(view.module, url_prefix="/%s" % name)
        except ValueError, e:
            pass
    
    create_default_views(app)

    return app

def create_db(app, db):
    ctx = app.test_request_context()
    ctx.push()
    db.create_all()
    ctx.pop()
    
def create_default_views(app):
    from myvault.views import default_views
    default_views(app)

def need_update():
    #update_url = "http://sourceforge.net/projects/themycubevault/files/current.txt/download"
    update_url = "http://192.168.170.141:9000/current.txt"
    try:
        latest_version = urllib2.urlopen(update_url, timeout=5).read()

        if latest_version.strip() > VERSION:
            return True
    except Exception, e:
        #print "failed downloading version file. %r" % e
        pass

    return False

def uniq(seq):
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]

def update_version(app, db):

    logger = app.logger
    ctx = app.test_request_context()
    ctx.push()
    from myvault.models import AppVersion

    current_installed = AppVersion.query and \
            AppVersion.query\
                .order_by('version DESC')\
                .first()
    
    installed_version = current_installed.version if current_installed else "0"

    scripts = []
    for script in os.listdir(os.path.join(app.config['APP_DIR'], "scripts")):
        if script.startswith('version'):
            scripts.append(script.split('.')[0])
    scripts.append("version_%s" % VERSION.replace(".", "_"))
    scripts = uniq(scripts)
    scripts.sort()

    if installed_version < VERSION:
        for script in scripts:
            if script > ("version_%s" % installed_version.replace(".", "_")):
                # if update script is missing. update version in db.
                # if update script is present and update script fails we don't update version in db.
                update_script = None
                try:
                    update_script = import_string("scripts.%" % script)
                except:
                    pass

                try:
                    if update_script:
                        update_script.update(app, db)
                except Exception, e:
                    logger.warn("%r", e)
                    raise e
                    
                update_version = script.split("_", 1)[1].replace("_", ".")
                new_version = AppVersion(version=update_version)
                db.session.add(new_version)
                db.session.commit()
    
    ctx.pop()
    return True


# vim: set et sts=4 ts=4 sw=4:
