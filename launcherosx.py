#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""

import sys
import os


sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))

import subprocess
import time
import signal
import urllib
import urllib2
import re
from multiprocessing import freeze_support

import objc
from Foundation import *
from AppKit import NSApp, NSApplication,NSGetAlertPanel,NSReleaseAlertPanel
from PyObjCTools import AppHelper
import webbrowser
import systrayosx
from socket import *
from settings import HOST

import version
from myvault.helpers import pscan

def startService_(self, notification):
    """
    Look for an open port then start the webservice on that port.
    """
    
    if not hasattr(self, 'server_pid') or self.server_pid is None:
        #print sys.executable
        self.server_process = subprocess.Popen([sys.executable, 'server.py', self.server_port])
       
        self.server_pid = self.server_process.pid
        
        #self.disabled_menuitems.remove('Stop')
        self.disabled_menuitems.remove('Open Dashboard')
        
        self.disabled_menuitems.append('Start')

def restartService_(self, notification):
    """
    Restart the server.
    """
    if not hasattr(self, 'server_pid') or self.server_pid is None:
        self.server_process = subprocess.Popen([sys.executable, 'server.py', self.server_port])
        self.server_pid = self.server_process.pid
    else:
        try:
            try:
                urllib2.urlopen("http://%s:%s/stop" % (HOST, self.server_port), timeout=2)
            except Exception, e:
                pass
            self.server_process.wait()
            self.server_pid = None
        except IOError, e:
            pass

        self.server_process = subprocess.Popen([sys.executable, 'server.py', self.server_port])
        self.server_pid = self.server_process.pid


def stopService_(self, notification):
    """
    Stop the webservice but not quit the program.
    """
    if hasattr(self, 'server_pid') and self.server_pid:
        try:
            try:
                urllib2.urlopen("http://%s:%s/stop" % (HOST, self.server_port), timeout=1)
            except Exception:
                pass
            self.server_process.wait()
            self.server_pid = None
        except IOError, e:
            pass
        
        self.disabled_menuitems.remove('Start')
        
        #self.disabled_menuitems.append('Stop')
        self.disabled_menuitems.append('Open Dashboard')
        

def openDashboard_(self, notification):
    webbrowser.open_new("http://%s:%s" % (HOST, self.server_port))

def quitServices_(self, notification):
    """
    Stop the webservice and quit the program.
    """
    if hasattr(self, 'server_pid') and self.server_pid:
        try:
            try:
                urllib2.urlopen("http://%s:%s/stop" % (HOST, self.server_port), timeout=1)
            except Exception:
                pass
            self.server_process.wait()
            self.server_pid = None
        except IOError, e:
            pass

    # give time to subprocess to cleanup itself
    time.sleep(1)
    NSApp().terminate_(self)
    
def toggleOpenAtLogin_(self, notification):
    #is it really safe to assume its always run from there   
    os.system("defaults write ~/Library/Preferences/loginwindow AutoLaunchedApplicationDictionary -array-add '{Path = \"/Applications/MyCube\ Vault.app\" ; }'")
    print 'toggleOpenAtLogin'

def resetPassword_(self,notification):
    #message = "This will reset your password. Are you sure?"
    #response = win32ui.MessageBox(
    #        message,
    #        "MyVault",
    #        win32con.MB_YESNO)
    #if response == win32con.IDYES:
    #doTest()
    try:
        from settings import db, app
        from models import Account, Session
        
        ctx = app.test_request_context()
        ctx.push()
        account = Account.query and Account.query.first()
        if account:
            db.session.delete(account)
            db.session.commit()
            
        sessions = Session.query and Session.query.all()
        if sessions:
            for session in sessions:
                db.session.delete(session)
            db.session.commit()
            
        ctx.pop()
        
        if hasattr(self, 'server_pid') and self.server_pid:
            webbrowser.open("http://%s:%s/logout" % (HOST, self.server_port))
    except:
        pass

def doTest():
    alertPanel = None
    modalSession = None
    app = NSApplication.sharedApplication()
    try:
        alertPanel = NSGetAlertPanel(
                "Please wait", "Bla bla bla", None, None, None)
        modalSession = app.beginModalSessionForWindow_(alertPanel)

        print modalSession
        time.sleep(1)
    finally:
        if modalSession is not None:
            app.endModalSession_(modalSession)
            modalSession = None

        if alertPanel is not None:
            NSReleaseAlertPanel(alertPanel)
            alertPanel = None


if __name__ == "__main__":
    freeze_support()
    def restartCallback_(self, notification):
        try:
            data = urllib2.urlopen("http://%s:%s/check_restart" % (HOST, self.server_port), timeout=2).read()
            if data == "true":
                self.restartService_("")
        except Exception, e:
            pass

    objc.classAddMethod(systrayosx.Backup, "restartCallback_", restartCallback_)
    objc.classAddMethod(systrayosx.Backup, "restartService_", restartService_)

    app = NSApplication.sharedApplication()
    menus = [
       (('Open Dashboard', 'openDashboard:', ''), openDashboard_),
        (('Start', 'startService:', ''), startService_),
        #(('Stop', 'stopService:', ''), stopService_),
        (('Quit', 'quitServices:', ''), quitServices_)
        #(('Open at Login', 'toggleOpenAtLogin:', ''), toggleOpenAtLogin_),
        #(('Reset Password', 'resetPassword:', ''), resetPassword_)
     ]
    delegate = systrayosx.Backup.alloc().initWithMenus(menus)
    delegate.disabled_menuitems = ['Open Dashboard']
    delegate.server_port = str(pscan())
    delegate.startService_("")
    
    NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        3, delegate, "restartCallback_", None, YES)

    time.sleep(5)
    delegate.openDashboard_("")
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()


# vim: set et sts=4 ts=4 sw=4:
