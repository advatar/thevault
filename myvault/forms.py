"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""

from flaskext.wtf import Form, Required, TextField, BooleanField,\
    SelectField, CheckboxInput, SelectMultipleField,\
    RadioField, widgets

class AppSettingsForm(Form):
    run_at_startup = BooleanField('Run at Startup')
    backup_dir = TextField("Backup Data Dir")

# vim: set et sts=4 ts=4 sw=4:
