"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""

import os
import sys
import time
import datetime
import calendar
import logging
import urllib2
import threading
import Queue
from operator import itemgetter
from socket import gethostbyname, socket,\
        AF_INET, SOCK_STREAM
import imports
import simplejson as json
import atom
from flask import url_for
from settings import BACKUP_DIR, HOST

def get_logger():
    return logging.getLogger("myvaultapp")

def pscan(start=8000):
    targetIP = gethostbyname('127.0.0.1')
    for i in range(start, start+1000):
        s = socket(AF_INET, SOCK_STREAM)
        result = s.connect_ex((targetIP, i))
        if result > 0:
            s.close()
            return i

def create_folder(*args):
    path = os.path.join(*args)
    try:
        os.makedirs(path, mode=0766)
        return path
    except OSError, e:
        return path


def utc_to_local(t):
    """Converts UTC time to localtime.

    Accepts a utc struct_time and return a localtime struct_time.
    sourced: http://feihonghsu.blogspot.com/2008/02/converting-from-local-time-to-utc.html

    >>> utc_time = time.strptime("2010-09-15T20:37:39+0000", "%Y-%m-%dT%H:%M:%S+0000")
    >>> print time.strftime("%Y-%m-%d %H:%M:%S", utc_to_local(utc_time))
    2010-09-16 04:37:39

    """
    secs = calendar.timegm(t)
    return time.localtime(secs)

def to_ampm(s):
    """Converts time string like 0700 to 07:00 AM

    Accepts a string time in 0000 format and returns a string in 00:00 AM/PM format.

    >>> t = "0700"
    >>> to_ampm(t)
    '07:00 AM'
    
    >>> t = "1830"
    >>> to_ampm(t)
    '06:30 PM'

    """
    
    t = time.strptime(s, "%H%M")
    return time.strftime("%I:%M %p", t)

def from_ampm(s):
    """Converts time string like 07:00 AM to 0700

    Accepts a string time in 00:00 AM/PM format and returns a string in 0000 format.

    >>> t = "07:00 AM"
    >>> from_ampm(t)
    '0700'

    >>> t = "06:30 PM"
    >>> from_ampm(t)
    '1830'

    """

    t = time.strptime(s, "%I:%M %p")
    return time.strftime("%H%M", t)

def stringify_unicode_keys(value):
    """Converts unicode dictionary keys to string.
    Used mainly after loading a json object.

    """
    result = {}
    for k, v in value.iteritems():
        if hasattr(v, 'keys'):
            v = stringify_unicode_keys(v)
        result[str(k)] = v
    return result


def backup_dates_for_week(target_date, backup_days):
    """Get the backup dates for a given week
    based on the date given and desired days.

    Parameters:
        target_date - The date
        backup_days - an array of integers with 0 as Monday and 6 as Sunday
    Returns an array of datetime.datetime objects in descending order.

    >>> target = datetime.datetime(2010, 9, 24, 10, 0, 1)
    >>> backup_dates_for_week(target, [2, 4])
    [datetime.datetime(2010, 9, 24, 10, 0, 1), datetime.datetime(2010, 9, 22, 10, 0, 1)]

    """
    weekday = target_date.weekday()
    delta = datetime.timedelta(weeks=1)
    first_day = target_date - datetime.timedelta(days=weekday)

    backup_dates = []
    for day in backup_days:
        delta = datetime.timedelta(days=day)
        backup_dates.append(first_day + delta)

    backup_dates.sort()
    backup_dates.reverse()
    return backup_dates


def backup_dates_for_month(target_date, backup_days):
    """Get the backup dates for the given month and array of days.

    Parameters:
        target_date - datetime.datetime object
        backup_days - array of integers with 1 as first day of the month

    Returns an array of datetime.datetime objects.

    >>> target = datetime.datetime(2010, 9, 24, 10, 0, 1)
    >>> backup_dates_for_month(target, [10])
    [datetime.datetime(2010, 9, 10, 10, 0, 1)]

    """
    backup_dates = []
    cal = calendar.Calendar()
    month_days = [day for day in cal.itermonthdays(target_date.year, target_date.month) if day > 0]
    for day in backup_days:
        if day in month_days:
            backup_date = datetime.datetime(
                    target_date.year,
                    target_date.month,
                    day,
                    target_date.hour,
                    target_date.minute,
                    target_date.second)
            backup_dates.append(backup_date)
    backup_dates.sort()
    backup_dates.reverse()
    return backup_dates[:]


def get_last_daily_backup_schedule(current_date, schedule):
    """Get the last daily scheduled backup date.

    Parameters:
        current_date - datetime.datetime object
        schedule - dict with interval as key with following values: daily,
            weekly and monthly. This is ignored for now.

    Returns a datetime.datetime object

    >>> current_date = datetime.datetime(2010, 9, 24, 10, 0, 1)
    >>> get_last_daily_backup_schedule(current_date, None)
    datetime.datetime(2010, 9, 23, 10, 0, 1)

    """
    delta = datetime.timedelta(days=1)
    return current_date - delta


def get_last_weekly_backup_schedule(current_date, schedule):
    """Get the last daily scheduled backup date.

    Parameters:
        current_date - datetime.datetime object
        schedule - dict with key 'dayofweek' having an array of integers as
        value standing for days of the week starting from 0 as monday.

    Returns a datetime.datetime object

    >>> current_date = datetime.datetime(2010, 9, 24, 10, 0, 1)
    >>> get_last_weekly_backup_schedule(current_date, {'dayofweek': ['2']})
    datetime.datetime(2010, 9, 22, 10, 0, 1)

    """
    curdate = current_date
    delta = datetime.timedelta(weeks=1)
    previous_date = current_date
    while True:
        backup_days = map(lambda x: int(x), schedule['dayofweek'])
        backup_dates = backup_dates_for_week(current_date, backup_days)
        for backup_date in backup_dates:
            if curdate.date() > backup_date.date():
                return backup_date
            previous_date = backup_date
        
        current_date = current_date - delta


def get_last_monthly_backup_schedule(current_date, schedule):
    """Get the last monthly backup schedule

    Parameters:
        current_date - datetime.datetime object
        schedule - dict having 'dayofmonth' key with an array of integer value
        with 1 as first day of the month.

    Returns a datetime.datetime object

    >>> target_date = datetime.datetime(2010, 9, 24, 10, 0, 1)
    >>> get_last_monthly_backup_schedule(target_date, {'dayofmonth': [10]})
    datetime.datetime(2010, 9, 10, 10, 0, 1)

    """
    curdate = current_date
    while True:
        backup_days = map(lambda x: int(x), schedule['dayofmonth'])
        backup_dates = backup_dates_for_month(current_date, backup_days)
        previous_date = current_date

        for backup_date in backup_dates:
            if curdate.date() > backup_date.date():
                return backup_date
            previous_date = backup_date

        current_date = datetime.datetime(
                current_date.year,
                current_date.month - 1,
                1,
                current_date.hour,
                current_date.minute,
                current_date.second)

def get_backup_dates(current_date, schedule):
    if schedule['interval'] == 'daily':
        return [datetime.datetime(
                current_date.year,
                current_date.month,
                current_date.day)]
    elif schedule['interval'] == 'weekly':
        return backup_dates_for_week(
                current_date,
                map(lambda x: int(x), schedule['dayofweek']))
    elif schedule['interval'] == 'monthly':
        return backup_dates_for_month(
                current_date,
                map(lambda x: int(x), schedule['dayofmonth']))

def get_last_backup_schedule(current_date, schedule):
    if schedule['interval'] == 'daily':
        return get_last_daily_backup_schedule(current_date, schedule)
    elif schedule['interval'] == 'weekly':
        return get_last_weekly_backup_schedule(current_date, schedule)
    elif schedule['interval'] == 'monthly':
        return get_last_monthly_backup_schedule(current_date, schedule)

def backup_is_on_schedule(current_date, last_backup, schedule):
    """Check if we are on schedule

    Checking daily backup at 10pm. Current datetime is friday 10am.
    >>> schedule = {'interval': 'daily', 'timeofday': '2200'}
    >>> current_date = datetime.datetime(2010, 9, 24, 10, 0, 1)

    Last backup was wednesday 10pm should return False.
    >>> last_backup = datetime.datetime(2010, 9, 22, 22, 0, 1)
    >>> backup_is_on_schedule(current_date, last_backup, schedule)
    False

    Last backup was thursday 10pm should return True.
    >>> last_backup = datetime.datetime(2010, 9, 23, 22, 0, 1)
    >>> backup_is_on_schedule(current_date, last_backup, schedule)
    True

    Testing weekly backup every wednesday at 10pm.
    Current datetime is friday 10am.
    >>> schedule = {'interval': 'weekly', 'dayofweek': [2], 'timeofday': '2200'}
    >>> current_date = datetime.datetime(2010, 9, 24, 10, 0, 1)

    Last backup wednesday at 8pm should return True
    >>> last_backup = datetime.datetime(2010, 9, 22, 20, 0, 1)
    >>> backup_is_on_schedule(current_date, last_backup, schedule)
    True

    Last backup tuesday at 10pm should return False
    >>> last_backup = datetime.datetime(2010, 9, 21, 22, 0, 1)
    >>> backup_is_on_schedule(current_date, last_backup, schedule)
    False

    Testing monthly backup every 5th of the month at 10pm
    Current datetime is friday 10am.
    >>> schedule = {'interval': 'monthly', 'dayofmonth': [5], 'timeofday': '2200'}
    >>> current_date = datetime.datetime(2010, 9, 24, 10, 0, 1)
    
    Last backup 23rd of current month should return True
    >>> last_backup = datetime.datetime(2010, 9, 23, 10, 0, 1)
    >>> backup_is_on_schedule(current_date, last_backup, schedule)
    True

    Last backup 3rd of the current month should return False
    >>> last_backup = datetime.datetime(2010, 9, 3, 10, 0, 1)
    >>> backup_is_on_schedule(current_date, last_backup, schedule)
    False

    """
    # if we are current check if we need to backup right away for the day
    last_backup_schedule = get_last_backup_schedule(current_date, schedule)
    if last_backup.date() >= last_backup_schedule.date():
        if current_date.date() in [d.date() for d in get_backup_dates(current_date, schedule)]:
            today = datetime.datetime.today()
            run_time = datetime.datetime.strptime(schedule['timeofday'], "%H%M")
            run_schedule = datetime.datetime(
                    today.year,
                    today.month,
                    today.day,
                    run_time.hour,
                    run_time.minute)
            if last_backup.date() == today.date():
                return True
            if today < run_schedule:
                return True
        else:
            return True
    return False

class Worker(threading.Thread):
    def __init__(self, queue):
        self.queue = queue
        threading.Thread.__init__(self)
        self.daemon = True
        self.keep_running = True

    def run(self):
        running = True
        while running:
            try:
                func, args, kwargs = self.queue.get_nowait()
                func(*args, **kwargs)
            except Queue.Empty:
                running = self.keep_running

class WorkerPool(object):
    def __init__(self, worker_class, queue, workers=20):
        self.pool = []
        for i in range(workers):
            worker = worker_class(queue)
            self.pool.append(worker)

    def start(self):
        for worker in self.pool:
            worker.start()

    def stop(self):
        for worker in self.pool:
            worker.keep_running = False

        while len(self.pool) > 0:
            for k, v in enumerate(self.pool):
                if not v.is_alive():
                    self.pool.pop(k)


def get_pagination_params(request, default_page=None, default_per_page=None):
    try:
        page = int(request.values.get('page', default_page or 1))
    except ValueError, e:
        page = default_page or 1

    try:
        per_page = int(request.values.get('per_page', default_per_page or 10))
    except ValueError, e:
        per_page = default_per_page or 10

    return page, per_page


def get_archive_file(app_name, archive):
    file_path = os.path.join(
            BACKUP_DIR,
            app_name,
            archive)
    if archive.endswith(".atom"):
        return atom.FeedFromString(open(file_path).read())

    if archive.endswith(".json"):
        return json.load(open(file_path))

class Paginator(object):
    """Pagination for non-db backed list.

    >>> paginator = Paginator(['a','b','c','d','e','f','g','h','i', 'k'], page=2, per_page=2)
    >>> paginator.page_count()
    5
    >>> paginator.is_first_page()
    False
    >>> paginator.is_last_page()
    False
    >>> paginator.first_page()
    1
    >>> paginator.last_page()
    5
    >>> paginator.has_next
    True
    >>> paginator.has_prev
    True
    >>> paginator.next_num
    3
    >>> paginator.prev_num
    1
    >>> paginator.items
    ['c', 'd']
    >>> paginator.pages
    5

    """

    def __init__(self, all_items, page=None, per_page=None, key_id=None):

        if key_id is None:
            key_id = 'id'

        if hasattr(all_items, "keys"):
            items = all_items.values()
        else:
            items = all_items
        self.all_items = items
        self.page = page and int(page) or 1
        self.per_page = per_page and int(per_page) or 10

    def page_count(self):
        count = len(self.all_items)/self.per_page
        if (len(self.all_items) - count * self.per_page) > 0:
            count += 1
        return count

    def all_pages(self):
        if self.page_count() < 1:
	        return [1]
        return range(1, self.page_count() + 1)

    def iter_pages(self, surround=5):
        pages = self.all_pages()
        cur_page = pages.index(self.page)
        start_page = cur_page - surround
        if start_page < 0:
            start_page = 0
        end_page = cur_page + surround + 1
        
        if cur_page < surround:
            return pages[:surround * 2 + 1]

        if (len(pages) - cur_page) < surround:
            return pages[len(pages) - (surround * 2):]

        return pages[start_page:end_page]

    @property
    def pages(self):
        return len(range(1, self.page_count() + 1))

    def is_first_page(self):
        return self.page == self.first_page()

    def is_last_page(self):
        return self.page == self.last_page()

    def first_page(self):
        return self.all_pages()[:1][0]

    def last_page(self):
        return self.all_pages()[-1:][0]

    @property
    def has_next(self):
        return self.page < self.last_page()

    @property
    def next_num(self):
        return self.page + 1

    @property
    def has_prev(self):
        return self.page > self.first_page()

    @property
    def prev_num(self):
        return self.page - 1

    @property
    def items(self):
        page = (self.page > 0 and self.page or 1) - 1
        per_page = self.per_page
        start = page * per_page
        end = start + per_page
        if hasattr(self.all_items, 'keys'):
            ks = self.all_items.keys()[start:end]
            new_items = []
            for k in ks:
                new_items.append(self.all_items[k])
            return new_items
        else:
            return self.all_items[start:end]


class PhotoPaginator(object):
    """Paginator for paginating individual pages

    >>> photos = [{'photo': 'photo 1', 'id': '3'}, {'photo':'photo 2', 'id':'1'}, {'photo':'photo 3', 'id': '2'}]
    >>> paginator = PhotoPaginator(photos, '1')
    >>> paginator.photos
    [{'photo': 'photo 1', 'id': '3'}, {'photo': 'photo 2', 'id': '1'}, {'photo': 'photo 3', 'id': '2'}]
    >>> paginator.photo_id
    '1'
    >>> paginator.previous_photo_id
    '3'
    >>> paginator.next_photo_id
    '2'
    >>> paginator.current_photo
    {'photo': 'photo 2', 'id': '1'}
    >>> paginator.next_photo
    {'photo': 'photo 3', 'id': '2'}
    >>> paginator.previous_photo
    {'photo': 'photo 1', 'id': '3'}
    >>> paginator.photo_of_total
    2

    """

    def __init__(self, photos, photo_id, key_id=None):
        """
        Parameters:
            photos - list of photos dict with id as part of dict.
            photo_id - the current photo being viewed.

        """
        if key_id is None:
            key_id = 'id'

        if hasattr(photos, 'keys'):
            self.photos = photos.values()
        else:
            self.photos = photos
        
        self.photo_ids = [x[key_id] for x in self.photos] 
        self.all_items = self.photos
        self.photo_id = photo_id

    @property
    def items(self):
        return self.all_items

    @property
    def current_photo_index(self):
        return self.photo_ids.index(self.photo_id)

    @property
    def current_photo(self):
        return self.all_items[self.current_photo_index]

    @property
    def next_photo_id(self):
        next_index = self.next_photo_index
        if next_index is not None:
            return self.photo_ids[next_index]
        return None

    @property
    def next_photo_index(self):
        if self.current_photo_index < (len(self.photos) - 1):
            return self.current_photo_index + 1
        return None

    @property
    def next_photo(self):
        return self.all_items[self.next_photo_index]

    @property
    def previous_photo_id(self):
        previous_index = self.previous_photo_index
        if previous_index is not None:
            return self.photo_ids[previous_index]
        return None

    @property
    def previous_photo_index(self):
        if self.current_photo_index > 0:
            return self.current_photo_index - 1
        return None

    @property
    def previous_photo(self):
        return self.all_items[self.previous_photo_index]

    def photos_count(self):
        return len(self.photos)

    @property
    def photo_of_total(self):
        return self.current_photo_index + 1

def is_online():
    try:
        import socket
        if HOST == "127.0.0.1":
            return False
        host = socket.gethostbyaddr(HOST)
        return True
    except Exception, e:
        return False

