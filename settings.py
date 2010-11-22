"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""

import os, sys
from flask import Flask
import cherrypy
from myvault.database import db
import myvault.models
from werkzeug import import_string
import logging, logging.handlers
import ConfigParser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

import kronos

USBMODE = False

def get_path(target):
    path = os.path.dirname(os.path.realpath(__file__))
    if path.endswith('library.zip'):
        new_path = os.path.sep.join(path.split(os.path.sep)[:-1] + [target])
    else:
        new_path = os.path.sep.join(path.split(os.path.sep) + [target])
    return new_path

HOST = "localhost.mycube.com"

try:
    import socket
    host = socket.gethostbyaddr(HOST)
except Exception, e:
    print "%r" % e
    HOST = '127.0.0.1'

try:
    PORT = int(sys.argv[1])
except:
    PORT = 8000

APP_DIR = os.path.dirname(__file__)
if sys.platform == "win32":
    import winhelpers
    folders = winhelpers.get_user_folders()
    APP_DIR = os.path.join(folders['AppData'], 'MyCube Vault')
    BACKUP_DIR = os.path.join(folders['AppData'], 'MyCube Vault')
elif sys.platform == 'darwin':
    BACKUP_DIR = "%s/Library/Application Support/MyCube Vault" % os.environ['HOME']
    #APP_DIR = "%s/Library/Application Support/MyCube Vault" % os.environ['HOME']
    APP_DIR = os.getcwd()
else:
    APP_DIR = os.path.dirname(os.path.realpath(__file__)) 
    BACKUP_DIR = os.path.join(os.path.expanduser('~'), '.mycube')

#BACKUP_DIR = os.getcwd()
if USBMODE:
    APP_DIR = os.getcwd()
    BACKUP_DIR = os.path.join(APP_DIR, os.path.pardir, 'Data')

print "APP_DIR", APP_DIR
config_parser = ConfigParser.ConfigParser()
BRIDGE = "https://opensocialgraph.appspot.com/backup_bridge/facebook/authorize"

try:
    config_parser.readfp(open(os.path.join(APP_DIR, "config.ini")))
    BRIDGE = config_parser.get("MyCube Vault", "bridge")
except:
    pass

DEBUG = False
SECRET_KEY = "asdfasdfasfsadf"
SQLALCHEMY_DATABASE_URI = "sqlite:////%s/mc.db" % os.path.sep.join(BACKUP_DIR.split(os.path.sep)[1:])
SQLALCHEMY_ECHO = False
KRON = kronos.ThreadedScheduler()
KRON.tasks = {}

GOOGLE_OAUTH_CONSUMER_KEY = "opensocialgraph.appspot.com"
GOOGLE_OAUTH_CONSUMER_SECRET = "ZwKQP4ILJ5G6witkPvCz7Jzx"

def create_app(config=None):
    app = Flask("myvaultapp")

    app.config.from_object(__name__)
    
    if config is not None:
        app.config.from_object(config)

    try:
        os.makedirs(BACKUP_DIR, mode=0766)
        os.makedirs(APP_DIR, mode=0766)
    except OSError, e:
        pass

    for d in ["applications"]:
        path = os.path.join(APP_DIR, d)
        sys.path.insert(0,path)


    from myvault.scheduler import init_scheduler
    init_scheduler(app)

    logger = app.logger
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    print os.path.join(BACKUP_DIR, 'myvault.log')
    rh = logging.handlers.RotatingFileHandler(os.path.join(BACKUP_DIR, 'myvault.log'))
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
        applications_path = os.path.join(APP_DIR,"applications")
    else:
        applications_path = get_path("applications") 
    
    print "applications path", applications_path

    sys.path.insert(0, applications_path)
    
    for name in os.listdir(applications_path):
        try:
            view = import_string("%s.views" % name)
            if name == "base":
                mount = ""
                app.register_module(view.module, url_prefix="/%s" % mount)
            #if name == 'picasaweb_app':
            #    continue
            app.register_module(view.module, url_prefix="/%s" % name)
        except ValueError, e:
            pass
    
    create_default_views(app)
    try:
        os.makedirs(BACKUP_DIR, mode=0766)
        os.makedirs(APP_DIR, mode=0766)
    except OSError:
        pass

    return app

def create_db(app, db):
    ctx = app.test_request_context()
    ctx.push()
    db.create_all()
    ctx.pop()
    
def create_default_views(app):
    from myvault.views import default_views
    default_views(app)
 
