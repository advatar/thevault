#!/usr/bin/env python -OO
#
# Copyright 2008-2010 The SABnzbd-Team <team@sabnzbd.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# This script has been edited to work for MyCube Vault.

from distutils.core import setup

import glob
import sys
import os
import platform
import tarfile
import re
import subprocess
import shutil

#try:
#    import py2exe
#except ImportError:
#    py2exe = None

if sys.platform == 'darwin':
    try:
        import py2app
        from setuptools import setup
    except ImportError:
        py2app = None

    VERSION_FILE = 'version.py'
    VERSION_FILEAPP = 'osx/resources/InfoPlist.strings'


    def CheckPath(name):
        if os.name == 'nt':
            sep = ';'
            ext = '.exe'
        else:
            sep = ':'
            ext = ''

        for path in os.environ['PATH'].split(sep):
            full = os.path.join(path, name+ext)
            if os.path.exists(full):
                return name+ext
        print "Sorry, cannot find %s%s in the path" % (name, ext)
        return None


    SvnVersion = CheckPath('svnversion')
    SvnRevert = CheckPath('svn')
    ZipCmd = CheckPath('zip')
    UnZipCmd = CheckPath('unzip')
    if os.name == 'nt':
        NSIS = CheckPath('makensis')
    else:
        NSIS = '-'

    if not (SvnVersion and SvnRevert and ZipCmd and UnZipCmd and NSIS):
        exit(1)

    SvnRevertApp =  SvnRevert + ' revert '
    SvnUpdateApp = SvnRevert + ' update '
    SvnRevert =  SvnRevert + ' revert ' + VERSION_FILE

    if len(sys.argv) < 2:
        target = None
    else:
        target = sys.argv[1]

    if target not in ('source', 'binary', 'installer', 'app'):
        print 'Usage: setup.py app'
        exit(1)

    # Derive release name from path
    base, release = os.path.split(os.getcwd())
    release = '0.1'
    prod = 'MyVault-' + release
    prod2 = 'MyCubeVault-alpha'

    fileDmg = prod + '-osx.dmg'
    fileImg = prod + '.sparseimage'

    fileDmg2 = prod2 + '-osx.dmg'
    fileImg2 = prod2 + '.dmg'
    volume = "/Volumes/MyVault/"
    volume2 = "/Volumes/MyCube\ Vault/"


    #if not platform.system() == 'Darwin':
    #    print "Sorry, only works on Apple OSX!"
    #    os.system(SvnRevert)
    #    exit(1)
    sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))       
    sys.argv[1] = 'py2app'
    os.system('rm -rf __MACOSX>/dev/null')
    os.system('rm -rf %s>/dev/null' % fileDmg2)
    #Create sparseimage from template
    #os.system("unzip myvault-template.sparseimage.zip")
    #os.rename('myvault-template.sparseimage', fileImg)
    
    os.system("unzip mycube-template.dmg.zip")
    os.rename('mycube-template.dmg', fileImg2)

    #mount sparseimage
    #os.system("hdiutil mount %s" % (fileImg))
    os.system("hdiutil mount %s" % (fileImg2))
    
    

    import launcherosx

    APP = ['launcherosx.py']
    #DATA_FILES = ['mc.db',"templates", 'icons','static','static/js','static/css','static/images']
    DATA_FILES = ["templates", 'icons','static','static/js','static/css','static/images','applications', 'scripts']
     
    OPTIONS = {'argv_emulation': True,
        'packages':[ 'cherrypy','jinja2','flask','sqlalchemy.dialects.sqlite','flaskext','flaskext.wtf','werkzeug','simplejson','sqlalchemy','wtforms'],
       'iconfile': 'icons/MyVault.icns',
       'plist': {
       'NSUIElement':1,
       #'LSUIElement':1,
       'RunAtLoad':'true',
       'CFBundleName':'MyCube Vault',
       'CFBundleShortVersionString':release,
       'NSHumanReadableCopyright':'MyCube',
       'CFBundleIdentifier':'com.mycube.vault'
       }}
           

    setup(
        app=APP,
        data_files=DATA_FILES,
        options={'py2app': OPTIONS },
        setup_requires=['py2app'],
    )
    
    
    os.system("cp config.py dist/MyCube\ Vault.app/Contents/Resources")
    #os.system("cp -r applications dist/MyCube\ Vault.app/Contents/Resources")
    os.system("cp server.py dist/MyCube\ Vault.app/Contents/Resources")
    os.system("cp -p icons/MyVault.icns dist/MyCube\ Vault.app/Contents/Resources>/dev/null")
    os.system("rm -rf dist/MyCube\ Vault.app/Contents/Resources/PythonApplet.icns>/dev/null")
    
    #os.system("cp -p osx/resources/update dist/myvault.app/Contents/Resources>/dev/null")
 
    #os.system("chmod +x dist/MyCube\ Vault.app/Contents/Resources/update>/dev/null")
    # remove svn sludge
    os.system("find dist/MyCube\ Vault.app -name .svn | xargs rm -rf")

    #copy built app to mounted sparseimage
    #os.system("cp -r dist/MyVault.app %s>/dev/null" % volume)
    os.system("cp -r dist/MyCube\ Vault.app %s >/dev/null" % volume2)
    os.system("cp license %s >/dev/null" % volume2)

    #cleanup src dir
    os.system("rm -rf dist/>/dev/null")
    os.system("rm -rf build/>/dev/null")
    #os.system("find ./ -name *.pyc | xargs rm")
 
    #Wait for enter from user
    #For manually arrange icon position in mounted Volume...
    #wait = raw_input ("Arrange Icons in DMG and then press Enter to Finalize")
    print 'eject'
    #Unmount sparseimage
    os.system("hdiutil eject /Volumes/MyCube\ Vault/>/dev/null")
    os.system("sleep 10")
    #Convert sparseimage to read only compressed dmg
    print 'compress and convert'
    os.system("hdiutil convert %s  -format UDBZ -o %s>/dev/null" % (fileImg2,fileDmg2))
    #Remove sparseimage
    os.system("rm %s>/dev/null" % (fileImg2))

else:
    try:
        from cx_Freeze import setup, Executable
    except ImportError:
        from setuptools import setup

    base = None
    mainscript = 'launcherwindows.py'
    if sys.platform == 'win32':
        base = 'Win32GUI'
    elif sys.platform == 'linux2':
        mainscript = 'launcherubuntu.py'
    else:
        print 'Platform not supported'
        exit(1)

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
    
    extra_options = dict(
            executables=[
                Executable(mainscript, base=base, icon='icons/mycubevaulticon.ico'),
                Executable('server.py', base=base)],
            description='A backup service',
            version="0.1",
            options={'build_exe': {
                'include_files': ['templates', 'static', 'icons',
                    'applications', 'config.ini', 'license.txt', 'scripts', 'Microsoft.VC90.MFC'],
                'packages': ['sqlalchemy','werkzeug','flask','jinja2','wtforms',
                    'gdata', 'atom'],},},)

    setup(name='MyCube Vault', **extra_options)

