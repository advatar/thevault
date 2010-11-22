import os, sys
from distutils.core import setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from esky.bdist_esky import Executable
#base = None
mainscript = "launcherwindows.py"

if sys.platform == "win32":
    #base = "Win32GUI"
    mainscript = "launcherwindows.py"
elif sys.platform == "linux2":
    mainscript = "launcherubuntu.py"
elif sys.platform == "darwin":
    mainscript = "launcherosx.py"

icon_file = os.path.join(os.path.dirname(__name__), "icons", "systrayicon.ico")
boot = Executable("launcher.py", icon=icon_file, name="myvault",
        gui_only=True)

launcher = Executable(mainscript,
        gui_only=True, icon=icon_file, include_in_bootstrap_env=False)

server = Executable('server.py', gui_only=True, include_in_bootstrap_env=False)

scripts = [boot, launcher, server]

includes = ['flask','werkzeug','werkzeug.local','werkzeug.serving',
        'sqlalchemy', 'flaskext.script', 'flaskext.sqlalchemy',
        'flaskext.wtf', 'flaskext.testing', 'wtforms', 'werkzeug.security']

cx_freeze_options = {
        'include-files': ['templates', 'static', 'icons', 'applications']}

options = {'bdist_esky':{
    'includes': includes,
    'freezer_module': 'cx_freeze',
    'freezer_options': cx_freeze_options}}

print "%r" % scripts
print "%r" % options

setup(
        name="MyVault",
        version="0.1",
        scripts=scripts,
        options=options)

