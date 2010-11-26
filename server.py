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

@app.route('/restart')
def restart_service():
    server.stop()
    KRON.stop()
    app = create_app()
    dispatcher = wsgiserver.WSGIPathInfoDispatcher({'/': app})
    server = wsgiserver.CherryPyWSGIServer((HOST, PORT), dispatcher)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

def stop_server(signum, frame):
    KRON.stop()
    server.stop()

#if __name__ == "__main__":
#    freeze_support()
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
    start_server()

# vim: set et sts=4 ts=4 sw=4:
