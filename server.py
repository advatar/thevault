#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""
import os
import sys
from multiprocessing import freeze_support

from imports import *

import flaskext.sqlalchemy

import cherrypy
from cherrypy import wsgiserver
from settings import create_app, create_db, HOST, PORT, KRON
from myvault.database import db
from myvault.models import AppMessage
import config
from myvault.helpers import get_logger


app = create_app(config)

dispatcher = wsgiserver.WSGIPathInfoDispatcher({'/': app})
server = wsgiserver.CherryPyWSGIServer((HOST, PORT), dispatcher)

logger = get_logger()

@app.route("/stop")
def stop_service():
    KRON.stop()
    server.stop()
    return "service stop"


def make_response(payload):
    """
    Creates a no-cache response. Handy for AJAX calls.
    """
    response = app.make_response(payload)
    response.headers['cache-control'] = 'no-cache'
    return response

@app.route('/restart')
def restart_service():
    """
    Add a restart server job.
    """
    app_message = AppMessage(topic='server_restart', message='restart')
    db.session.add(app_message)
    db.session.commit()
    return make_response("restarting")

def stop_server(signum, frame):
    KRON.stop()
    server.stop()

def start_server():
    create_db(app, db)
    KRON.start()

    try:
        logger.debug("starting server in %s:%s", HOST, PORT)
        server.bind_addr = (HOST, PORT)
        server.start()
    except KeyboardInterrupt:
        server.stop()

if __name__ == "__main__":
    freeze_support()
    start_server()

# vim: set et sts=4 ts=4 sw=4:
