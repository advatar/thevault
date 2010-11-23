"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""

from flaskext.wtf import Form, Required, TextField, BooleanField,\
        SelectField, CheckboxInput, SelectMultipleField,\
        RadioField, widgets

class ScheduleForm(Form):
    interval = SelectField('Interval',
            choices=[
                ('daily', 'Daily'),
                ('weekly', 'Weekly'),
                ('monthly', 'Monthly')])

    dayofweek = RadioField('Day',
            choices=[
                ('1', 'Monday'),
                ('2', 'Tuesday'),
                ('3', 'Wednesday'),
                ('4', 'Thursday'),
                ('5', 'Friday'),
                ('6', 'Saturday'),
                ('7', 'Sunday')])

    dayofmonth = SelectField('Day',
            choices=[(x,x) for x in range(1,32)],
            description="Schedules for 29, 30 or 31 may not run on months not ending in 29, 30 and 31")

    timeofday = TextField("Time")

    hourofday = SelectField('Time',
            choices=[(("%d" % x).zfill(2), ("%d" % x).zfill(2)) for x in range(1,13)])

    minuteofhour = SelectField('Minutes',
            choices=[(x,x) for x in ['00','15','30','45']])

    ampm = SelectField('AMPM',
            choices=[('AM', 'AM'), ('PM','PM')])

# vim: set et sts=4 ts=4 sw=4:
