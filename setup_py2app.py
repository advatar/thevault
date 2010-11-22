"""
 py2app/py2exe build script for MyApplication.

 Will automatically ensure that all build prerequisites are available
 via ez_setup

 Usage (Mac OS X):
 python setup_py2app.py py2app -p werkzeug,simplejson,sqlalchemy,jinja2,flask,flaskext,cherrypy

 Usage (Windows):
     python setup.py py2exe
     
     
"""
import ez_setup
import os
ez_setup.use_setuptools()

import sys
from setuptools import setup
 
if sys.platform == 'darwin':
     DATA_FILES = ['config.ini',"templates", 'static','icons','static/js','static/css','static/images', 'applications']
 
     mainscript = 'launcherosx.py'
     extra_options = dict(
         setup_requires=['py2app'],
         app=['launcherosx.py'],
         data_files= DATA_FILES,
         options=dict(py2app=dict(includes=['views'],packages=[
             'cherrypy','jinja2', 'jinja2.ext',
             'flask','sqlalchemy.dialects.sqlite','flaskext','flaskext.wtf','flaskext.sqlalchemy','werkzeug','simplejson','sqlalchemy','wtforms'],argv_emulation=True)),
     )
     
  
elif sys.platform == 'win32':
     mainscript = 'mcsti.py'
     extra_options = dict(
         setup_requires=['py2exe'],
         app=[mainscript],
     )
else:
     extra_options = dict(
         # Normally unix-like platforms will use "setup.py install"
         # and install the main script as such
         scripts=[mainscript],
     )

setup(
    name="myvault",
    **extra_options
)

os.system("cp server.py dist/myvault.app/Contents/Resources")
#os.system("chmod +x dist/myvault.app/Contents/Resources/mcbs>/dev/null")

