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
from google_auth import PicasaWeb
import simplejson as json

from myvault.helpers import Worker, WorkerPool, get_logger,\
        create_folder

from myvault.api import get_progress_monitor, add_to_archive
from settings import BACKUP_DIR, GOOGLE_OAUTH_CONSUMER_KEY,\
        GOOGLE_OAUTH_CONSUMER_SECRET

import gdata
from gdata import photos
from gdata.photos import service

logger = get_logger()

def run_backup(preference):
    logger.debug('running backup routing for picasaweb')
    logger.debug('preference: %r', preference)
    progress_monitor = get_progress_monitor('picasaweb_app')

    profile = preference['profile']

    access_token = preference['tokens']
    logger.debug('access tokens: %r', access_token)

    try:
        auth = PicasaWeb(GOOGLE_OAUTH_CONSUMER_KEY,
                GOOGLE_OAUTH_CONSUMER_SECRET,
                str(access_token['access_token']),
                str(access_token['access_token_secret']))
    except Exception, e:
        logger.debug('PicasaWeb auth: %r', e)
        raise e
    logger.debug('we got auth')
    try:
        profile = auth.get_profile()
    except Exception, e:
        logger.debug('error getting profile %r', e)
        raise e
    logger.debug('we got profile: %r', profile)    
    data = {'profile': profile}
    picasa_job_queue = Queue.Queue(1500)
    workers = WorkerPool(Worker, picasa_job_queue)
    workers.start()

    logger.debug('we got auth')
    progress_monitor.update(10)

    logger.debug('getting albums')
    albums = auth.google_api('/data/feed/api/user/default',
            {'kind': 'album'}, photos.UserFeedFromString)
   
    logger.debug('albums xml: %r', albums.ToString())
    data['albums'] = {}

    def func(hash_key, result_dict, client, album):
        album_photos = client.PhotoFeedFromString(
                urllib2.urlopen(album.GetPhotosUri()).read())
        fotos = {}
        for album_photo in album_photos.entry:
            photo = {'id': album_photo.gphoto_id.text}
            photo['title'] = album_photo.media.title.text
            photo['source'] = album_photo.content.src
            photo['thumbnail'] = album_photo.media.thumbnail[1].url
            photo['timestamp'] = album_photo.timestamp.text
            photo['updated'] = album_photo.updated.text
            photo['published'] = album_photo.published.text
            fotos[photo['id']] = photo

        result_dict['albums'][hash_key]['photos'] = fotos

    for album in albums.entry:
        photo_album = {'id': album.gphoto_id.text}
        photo_album['title'] = album.title.text
        photo_album['name'] = album.name.text
        photo_album['timestamp'] = album.timestamp.text
        photo_album['updated'] = album.updated.text
        photo_album['published'] = album.published.text
        photo_album['count'] = int(album.numphotos.text)
        logger.debug('album: %r', photo_album)

        data['albums'][album.gphoto_id.text] = photo_album

        picasa_job_queue.put((func, (photo_album['id'], data, photos, album,), {}))

    progress_monitor.update(10)

    workers.stop()

    dump_albums(data)
    dump_json(data, progress_monitor.start_time)

    filename = "%s.json" % progress_monitor.start_time.strftime("%Y%m%d%H%M%S")
    add_to_archive("picasaweb_app", filename, progress_monitor.start_time)

    progress_monitor.complete()
    logger.debug("picasaweb_app backup done")
    return progress_monitor.start_time


def dump_json(data, backup_time):
    path = create_folder(BACKUP_DIR, 'picasaweb_app')

    fd = open(os.path.join(path, '%s.json' % backup_time.strftime('%Y%m%d%H%M%S')), 'w')
    fd.write(json.dumps(data))
    fd.close()


def dump_albums(data):
    path = create_folder(BACKUP_DIR, 'picasaweb_app', 'albums')

    photo_queue = Queue.Queue(1500)

    workers = WorkerPool(Worker, photo_queue)
    workers.start()

    for album_id, album in data['albums'].iteritems():
        album_path = create_folder(path, album['id'])

        downloaded_photos = os.listdir(album_path)

        for photo_id, photo in album['photos'].iteritems():
            if photo_id not in downloaded_photos:
                photo_path = create_folder(album_path, photo_id)
                photo_queue.put((dump_photo_set, (photo_path, photo,),{}))
            else:
                if not photo_exists(album_path, photo):
                    photo_path = create_folder(album_path, photo['id'])
                    photo_queue.put((dump_photo_set, (photo_path, photo,), {}))
                else:
                    pass
    workers.stop()


def dump_photo_set(photo_path, photo):
    try:
        dump_photo(photo['source'], os.path.join(photo_path, "photo.jpg"))
        time.sleep(1)
        dump_photo(photo['thumbnail'], os.path.join(photo_path, "thumbnail.jpg"))
    except Exception, e:
        logger.debug("%r", e)

def photo_exists(album_path, photo, ext=".jpg"):
    photo_path = os.path.join(album_path, photo['id'])
    return os.path.exists(os.path.join(photo_path, "thumbnail.jpg")) and\
            os.path.exists(os.path.join(photo_path, "photo.jpg"))

def dump_photo(url, path):
    try:
        img = download_media(url, "image/jpeg")
        write_media_data(path, img)
    except:
        img = download_media(url, "image/jpeg")
        write_media_data(path, img)

def download_media(url, mime_type=None):
    try:
        res = urllib.urlopen(url)
    except HTTPError, e:
        logger.debug("error %r while downloading %s", e, url)

    logger.debug("url: %s || content-type: %s", url, res.headers['content-type'])

    if mime_type is not None:
        assert res.headers['content-type'] == mime_type

    return res.read()

def write_image_data(path, filename, data):
    path = os.path.join(path, filename)
    write_media_data(path, data)

def write_media_data(path, data):
    fd = open(path, "wb")
    fd.write(data)
    fd.close()

