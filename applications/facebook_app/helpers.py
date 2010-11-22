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
import facebook
import simplejson as json
from myvault.helpers import Worker, WorkerPool, get_logger,\
        create_folder

from myvault.api import get_progress_monitor, add_to_archive

from settings import BACKUP_DIR

logger = get_logger()

def run_backup(preference):
    logger.debug("running backup routine for facebook_app")
    logger.debug("preference: %r", preference)
    progress_monitor = get_progress_monitor("facebook_app")
    
    graph = facebook.GraphAPI(preference['tokens'])
    data = {'profile': graph.get_object('me')}
    facebook_job_queue = Queue.Queue(1500)

    logger.debug("starting workers")

    workers = WorkerPool(Worker, facebook_job_queue)
    workers.start()

    for k, v in preference['settings'].iteritems():
        progress_monitor.update(10)
        logger.debug("processing %s", k)
        if v:
            if k == 'albums':
                data[k] = {}

                def func(hash_key, result_dict, client, album):
                    logger.debug("fetching data for album %s", album['id'])
                    photos = {}
                    album_photos = [photo for photo in client.get_connections(album['id'], 'photos', limit=1000000)['data']]
                    album_photos = sorted(album_photos, key=itemgetter('created_time'), reverse=True)
                    
                    for photo in album_photos:
                        logger.debug("fetching comments for photo %s in album %s",
                                photo['id'], album['id'])
                        comments = [comment for comment in client.get_connections(photo['id'], 'comments', limit=1000000)['data']]
                        photo['comments'] = sorted(comments, key=itemgetter('created_time'))
                        photos[photo['id']] = photo

                    album['photos'] = photos
                    result_dict[hash_key][album['id']] = album

                for obj in graph.get_connections('me', 'albums', limit=1000000)['data']:
                    logger.debug("queueing album %s", obj['id'])
                    facebook_job_queue.put((func, (k, data, graph, obj,), {}))

            elif k == 'photos':
                data[k] = []
                logger.debug("fetching data for tagged photos")
                photos = graph.get_connections('me', k, limit=1000000)['data']

                def func(hash_key, result_dict, client, obj):
                    logger.debug("fetching comments for tagged photo %s", obj['id'])
                    comments = [comment for comment in client.get_connections(obj['id'], 'comments', limit=1000000)['data']]
                    obj['comments'] = comments
                    result_dict[hash_key].append(obj)
                    
                for photo in photos:
                    logger.debug("queueing comments for tagged photo %s", photo['id'])
                    facebook_job_queue.put((func, (k, data, graph, photo), {}))


            else:
                data[k] = []
                
                def func(hash_key, result_dict, client, id):
                    logger.debug("fetching data for %s %s", hash_key, id)

                    obj = client.get_object(id)

                    if hash_key in ['statuses', 'events']:
                        logger.debug("fetching comments for %s %s", hash_key, id)
                        comments = [comment for comment in client.get_connections(id, 'comments', limit=1000000)['data']]
                        obj['comment'] = sorted(comments, key=itemgetter('created_time'))

                    result_dict[hash_key].append(obj)

                for obj in graph.get_connections('me', k, limit=1000000)['data']:
                    logger.debug("queueing %s %s", k, obj['id'])
                    facebook_job_queue.put((func, (k, data, graph, obj['id'],), {}))

    progress_monitor.update(10)

    workers.stop()

    if 'albums' in data:
        dump_albums(data)

    if 'photos' in data:
        dump_photos(data)

    dump_profile_pics(data)
    dump_json(data, progress_monitor.start_time)

    filename = "%s.json" % progress_monitor.start_time.strftime("%Y%m%d%H%M%S")
    add_to_archive("facebook_app", filename, progress_monitor.start_time)

    progress_monitor.complete()
    logger.debug("facebook_app backup done")
    return progress_monitor.start_time

def dump_photo(url, path):
    try:
        img = download_media(url, "image/jpeg")
        write_media_data(path, img)
    except:
        img = download_media(url, "image/jpeg")
        write_media_data(path, img)

def dump_photo_set(photo_path, photo, ext):
    try:
        dump_photo(photo['source'], os.path.join(photo_path, "photo%s" % ext))
        time.sleep(1)
        dump_photo(photo['picture'], os.path.join(photo_path, "thumbnail%s" % ext))
    except Exception, e:
        logger.debug("%r", e)


def photo_exists(album_path, photo, ext=".jpg"):
    photo_path = os.path.join(album_path, photo['id'])
    return os.path.exists(os.path.join(photo_path, "thumbnail%s" % ext)) \
            and os.path.exists(os.path.join(photo_path, "photo%s" % ext))

def dump_albums(data):
    path = create_folder(BACKUP_DIR, 'facebook_app', 'albums')

    photo_queue = Queue.Queue(1500)

    workers = WorkerPool(Worker, photo_queue)
    workers.start()

    for album_id, album in data['albums'].iteritems():
        album_path = create_folder(path, album['id'])

        downloaded_photos = os.listdir(album_path)
        for photo_id, photo in album['photos'].iteritems():
            source_url = urlparse.urlparse(photo['source'])
            ext = re.match("^.*/([^/]+?(\.[^/]+)?)$", source_url.path).groups()[1]
            if not ext:
                ext = ''

            if photo['id'] not in downloaded_photos:
                photo_path = create_folder(album_path, photo['id'])
                photo_queue.put((dump_photo_set, (photo_path, photo, ext,), {}))
            else:
                # either thumbnail or photo is missing. redownloading set
                if not photo_exists(album_path, photo):
                    photo_path = create_folder(album_path, photo['id'])
                    photo_queue.put((dump_photo_set, (photo_path, photo, ext,), {}))
                else:
                    pass # photo is already in the filesystem

    workers.stop()


def dump_photos(data):
    path = create_folder(BACKUP_DIR, 'facebook_app', 'photos')
    photo_queue = Queue.Queue(1500)
    workers = WorkerPool(Worker, photo_queue)
    workers.start()

    downloaded_photos = os.listdir(path)

    for photo in data['photos']:
        photo_path = create_folder(path, photo['id'])

        if not photo['id'] in downloaded_photos:
            photo_queue.put((dump_photo_set, (photo_path, photo, ".jpg",), {}))
        else:
            if not photo_exists(path, photo):
                photo_queue.put((dump_photo_set, (photo_path, photo, ".jpg",), {}))
            else:
                pass # photo is alread in the filesystem

    workers.stop()


def dump_profile_pics(data):
    
    def func(photo_path, id):
        url = "http://graph.facebook.com/%s/picture" % id
        filename = "%s.jpg" % id

        try:
            img = download_media(url)
            write_image_data(photo_path, filename, img)
        except:
            try:
                img = download_media(url)
                write_image_data(photo_path, filename, img)
            except Exception, e:
                logger.debug("an exception occured while downloading media %s. ignoring..", url)
    
    path = create_folder(BACKUP_DIR, 'facebook_app', 'profile_pics')
    photo_queue = Queue.Queue(1500)

    workers = WorkerPool(Worker, photo_queue)
    workers.start()

    downloaded_photos = os.listdir(path)

    for friend in data['friends']:
        photo = "%s.jpg" % friend['id']

        if photo not in downloaded_photos:
            photo_queue.put((func, (path, friend['id'],), {}))

    workers.stop()

def dump_json(data, backup_time):
    path = create_folder(BACKUP_DIR, 'facebook_app')

    fd = open(os.path.join(path, "%s.json" % backup_time.strftime("%Y%m%d%H%M%S")), "w")
    fd.write(json.dumps(data))
    fd.close()

def download_media(url, mime_type=None):
    try:
        res = urllib.urlopen(url)
    except HTTPError, e:
        logger.debug("error %r while downloading %s", e, url)

    logger.debug("url: %s || content-type: %s", url, res.headers['content-type'])
    assert res.code == 200
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

