"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""
import time
from flask import url_for, current_app
import urllib2
from settings import HOST, PORT, KRON
from myvault.helpers import get_logger, is_online

logger = get_logger()

def init_scheduler(app):   
    def load_schedules():
        try:
            url = "http://%s:%s/load_schedules" % (HOST, PORT,)
            urllib2.urlopen(url, timeout=1)
        except Exception, e:
            pass

    KRON.add_single_task(load_schedules, 'load_schedules', 3, 'threaded', None, None)


def reload_schedules():
    try:
        url = "http://%s:%s/reload_schedules" % (HOST, PORT,)
        urllib2.urlopen(url, timeout=1)
    except Exception, e:
        pass


def cancel_schedule(taskname):
    if taskname in KRON.tasks:
        logger.debug("canceling %s", taskname)
        try:
            KRON.cancel(KRON.tasks[taskname])
            del KRON.tasks[taskname]
        except Exception, e:
            logger.debug("schedule cancel error: %r", e)

def schedule_runner(job, app_name):
    if is_online():
        job(app_name)

def add_daily_schedule(taskname, schedule, callback):
    logger.debug("adding daily schedule %s | %r | %r", taskname, schedule,
            callback)
    cancel_schedule(taskname)
    logger.debug("old schedule canceled")
    timeofday = time.strptime(schedule['timeofday'], "%H%M")
    
    task = KRON.add_daytime_task(
            schedule_runner, # method to run
            taskname, # taskname
            range(1,8), # days of the week
            None, # days of the month
            (timeofday.tm_hour, timeofday.tm_min), # time of the day
            'threaded',
            (callback,taskname,), # args to job method
            None) # kwargs to job method

    KRON.tasks[taskname] = task
    logger.debug("done adding schedule")


def add_weekly_schedule(taskname, schedule, callback):
    cancel_schedule(taskname)

    timeofday = time.strptime(schedule['timeofday'], "%H%M")
    daysofweek = map(lambda x: int(x) + 1, schedule['dayofweek'])
    task = KRON.add_daytime_task(
            schedule_runner,
            taskname,
            daysofweek,
            None,
            (timeofday.tm_hour, timeofday.tm_min),
            'threaded',
            (callback,taskname,),
            None)

    KRON.tasks[taskname] = task


def add_monthly_schedule(taskname, schedule, callback):
    cancel_schedule(taskname)
   
    timeofday = time.strptime(schedule['timeofday'], "%H%M")
    daysofmonth = map(lambda x: int(x) + 1, schedule['dayofmonth'])
    task = KRON.add_daytime_task(
            schedule_runner,
            taskname,
            None,
            daysofmonth,
            (timeofday.tm_hour, timeofday.tm_min + 1),
            'threaded',
            (callback,taskname,),
            None)

    KRON.tasks[taskname] = task


def add_schedule(taskname, schedule, callback):
    if schedule['interval'] == 'daily':
        add_daily_schedule(taskname, schedule, callback)
    elif schedule['interval'] == 'weekly':
        add_weekly_schedule(taskname, schedule, callback)
    elif schedule['interval'] == 'monthly':
        add_monthly_schedule(taskname, schedule, callback)


