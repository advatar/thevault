"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""

import time
import simplejson as json
from myvault.models import db, Archive, BackupProgress, Settings
from myvault.helpers import stringify_unicode_keys

import datetime

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
