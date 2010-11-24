# -*- coding: utf-8 -*-

"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""

import os
import re
import time
import datetime
import Queue
import threading
import urlparse
import urllib
import urllib2
from operator import itemgetter
from flask import current_app
from google_auth import GoogleContacts
import simplejson as json

from myvault.helpers import Worker, WorkerPool, get_logger,\
        create_folder

from myvault.api import get_progress_monitor, add_to_archive
from settings import BACKUP_DIR, GOOGLE_OAUTH_CONSUMER_KEY,\
        GOOGLE_OAUTH_CONSUMER_SECRET

logger = get_logger()

def run_backup(preference):
    logger.debug("running backup routing for google_contacts_app")
    logger.debug("preference: %r", preference)
    progress_monitor = get_progress_monitor("google_contacts_app")
    
    logger.debug("getting progress monitor")
    profile = preference['profile']

    access_token = preference['tokens']
    logger.debug("access_tokens: %r", access_token)

    auth = GoogleContacts(GOOGLE_OAUTH_CONSUMER_KEY,
            GOOGLE_OAUTH_CONSUMER_SECRET,
            str(access_token['access_token']),
            str(access_token['access_token_secret']))

    logger.debug("we got auth")
    progress_monitor.update(20)

    logger.debug("getting contacts")
    contacts = auth.get_contacts()
    logger.debug("%r", contacts.author[0].ToString())
    progress_monitor.update(60)

    filename = "%s.atom" % progress_monitor.start_time.strftime("%Y%m%d%H%M%S")
    add_to_archive("google_contacts_app", filename, progress_monitor.start_time)
    dump_atom(contacts.ToString(), progress_monitor.start_time)

    progress_monitor.complete()

    return progress_monitor.start_time

def dump_atom(data, backup_time):
    path = create_folder(BACKUP_DIR, "google_contacts_app")

    fd = open(os.path.join(path, "%s.atom" % backup_time.strftime("%Y%m%d%H%M%S")), "w")
    fd.write(data)
    fd.close()

