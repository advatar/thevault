# -*- coding: utf-8 -*-

"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""
import sys
import os
import time
import simplejson as json
from settings import APP_DIR
from myvault.models import db, Archive, BackupProgress, Settings,\
        UserPreference
from myvault.helpers import stringify_unicode_keys

import datetime

if sys.platform == "win32":
    import winhelpers
    import pythoncom

class ProgressMonitor(object):
    def __init__(self, module):
        self.start_time = datetime.datetime.now()
        self.progress = 0
        self.monitor = BackupProgress(
                module=module,
                progress=self.progress,
                started_at = self.start_time)
        
        db.session.add(self.monitor)
        db.session.commit()

    def update(self, value=10):
        self.progress += value
        self.monitor.progress = self.progress
        db.session.add(self.monitor)
        db.session.commit()
    
    def complete(self):
        self.monitor.progress = 100
        self.monitor.ended_at = datetime.datetime.now()
        db.session.add(self.monitor)
        db.session.commit()

def get_progress_monitor(module):
    return ProgressMonitor(module)

def get_backup_progress(module):
    monitor = BackupProgress.query and \
            BackupProgress.query\
                .filter_by(module=module)\
                .order_by('id DESC').first()

    return monitor

def add_to_archive(module, filename, archive_time):
    archive = Archive(
            module=module,
            filename=filename,
            archived_at=archive_time)

    db.session.add(archive)
    db.session.commit()

def clear_archives(module):
    archives = Archive.query and Archive.query\
            .filter_by(module=module).all()

    for archive in archives:
        db.session.delete(archive)

    db.session.commit()

def get_archives(module, order=None, limit=None):
    if order is None:
        order = "id DESC"

    archives = Archive.query and Archive.query\
            .filter_by(module=module)\
            .order_by(order).limit(limit).all()

    return archives

def get_archive(module, archive_id):
    archive = Archive.query and Archive.query\
            .filter_by(id=int(archive_id), module=module)\
            .order_by('id DESC').first()

    return archive

def get_recent_archive(module):
    archive = Archive.query and Archive.query\
            .filter_by(module=module)\
            .order_by('id DESC').first()

    return archive

def get_paginated_archives(module, page, per_page, order=None):
    if order is None:
        order = "id DESC"

    archives = Archive.query and Archive.query\
            .filter_by(module=module)\
            .order_by(order).paginate(page, per_page)

    return archives

def get_settings(module):
    settings = Settings.query and \
            Settings.query\
                .filter_by(module=module)\
                .order_by('id DESC').first()

    if settings:
        data = stringify_unicode_keys(json.loads(settings.data))
        if 'schedule' in data:
            data['schedule'].update(schedule_to_form_time(data['schedule']['timeofday']))
        return data
    return {}


def save_settings(module, data):
    settings = Settings.query and \
            Settings.query\
                .filter_by(module=module)\
                .order_by('id DESC').first()

    if 'schedule' in data:
        data['schedule'].update(schedule_from_form_time(data['schedule']))

    if settings:
        settings.data = json.dumps(data)
    else:
        settings = Settings(module=module, data=json.dumps(data))
    db.session.add(settings)
    db.session.commit()

def get_app_settings():
    preferences = UserPreference.query and \
            UserPreference.query.first()

    if preferences:
        return stringify_unicode_keys(json.loads(preferences.data))
    return {}

def save_app_settings(data):
    preferences = UserPreference.query and \
            UserPreference.query.first()

    if preferences:
        preferences.data = json.dumps(data)
    else:
        preferences = UserPreference(data=json.dumps(data))

    db.session.add(preferences)
    db.session.commit()


def get_tokens(service):
    tokens = Token.query and \
            Token.query\
                .filter_by(service=service)\
                .order_by('id DESC').first()

    if tokens:
        data = stringify_unicode_keys(json.loads(tokens.data))
        return data
    return {}

def save_tokens(service, data):
    tokens = Token.query and \
            Token.query\
                .filter_by(service=service)\
                .order_by('id DESC').first()

    if tokens:
        tokens.data = json.dumps(data)
    else:
        tokens = Token(service=service, data=json.dumps(data))
    db.session.add(tokens)
    db.session.commit()


def schedule_to_form_time(value):
    t = time.strptime(value, "%H%M")
    hour = time.strftime("%I", t)
    minute = time.strftime("%M", t)
    ampm = time.strftime("%p", t)
    return {'hourofday': hour, 'minuteofhour': minute, 'ampm': ampm}

def schedule_from_form_time(value):
    s = "%s:%s %s" % (value['hourofday'], value['minuteofhour'], value['ampm'])
    t = time.strptime(s, "%I:%M %p")
    return {'timeofday': time.strftime("%H%M", t)}


MACOSX_LAUNCH_AGENT_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.mycube.vault</string>
    <key>ProgramArguments</key>
    <array>
      <string>/Applications/MyCube Vault.app/Contents/MacOS/MyCube Vault</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
  </dict>
</plist>
"""

def run_at_startup(value):
    """
    Add/remove Startup Menu link (windows) or LaunchAgent Plist (MacOSX).
    """
    if sys.platform == "win32":
        try:
            pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        except pythoncom.com_error:
            pass

        folders = winhelpers.get_user_folders()
        filename = "MyCube Vault.lnk"
        path = os.path.join(folders['Startup'], 'MyCube Vault.lnk')
        working_dir = os.path.join(os.environ['PROGRAMFILES'], 'MyCube Vault')
        target = os.path.join(os.environ['PROGRAMFILES'], 'MyCube Vault', 'launcherwindows.exe')
        icon = os.path.join(os.environ['PROGRAMFILES'], 'MyCube Vault', 'icons', 'mycubevaulticon.ico')

        if value:
            winhelpers.create_shortcut(path, target, wDir=working_dir, icon=icon)
        else:
            if os.path.exists(path):
                os.remove(path)
        
        try:
            pythoncom.CoUnitialize()
        except Exception, e:
            pass

    elif sys.platform == 'darwin':
        filename = "com.mycube.vault.plist"
        plist = "%s/Library/LaunchAgents/%s" % (os.environ['HOME'], filename,)

        if value:
            fd = open(plist, "w")
            fd.write(MACOSX_LAUNCH_AGENT_PLIST)
            fd.close()
        else:
            if os.path.exists(plist):
                os.remove(plist)


# vim: set et sts=4 ts=4 sw=4:
