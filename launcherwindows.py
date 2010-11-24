#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""
import os
import sys
import subprocess
import time
import signal
import urllib
import urllib2
import re
import webbrowser
from multiprocessing import freeze_support
from systray import SysTray
import win32api
import win32con
#import win32ui
from myvault.helpers import pscan, is_online
from settings import HOST

def start_service(self):
    """
    Look for an open port then start the webservice on that port.
    """
    port = str(pscan())
    if not hasattr(self, 'server_pid') or self.server_pid is None:
        if re.search(r"python.*$", sys.executable):
            print "%r" % port
            print "%r" % sys.executable
            self.server_process = subprocess.Popen([sys.executable, 'server.py', port],
                    creationflags=win32con.CREATE_NEW_PROCESS_GROUP)
        else:
            path = os.path.dirname(sys.executable)
            print "executable path %r" % path
            server_path = os.path.join(path, 'server.exe')
            print "curdir %s" % os.getcwd()
            os.chdir(path)
            self.server_process = subprocess.Popen([server_path, port],
                    creationflags=win32con.CREATE_NEW_PROCESS_GROUP)

        self.server_pid = self.server_process.pid
        self.server_port = port
    
    # let's open the browser
    time.sleep(2)
    webbrowser.open("http://%s:%s" % (HOST, self.server_port))


def stop_service(self):
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


def open_dashboard(self):
    if not hasattr(self, "server_port") or not self.server_port:
        return None
    webbrowser.open("http://%s:%s" % (HOST, self.server_port))


def quit_services(self):
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
    time.sleep(2) 


def reset_password(self):
    """
    message = "This will reset your password. Are you sure?"
    response = win32ui.MessageBox(
            message,
            "MyVault",
            win32con.MB_YESNO)
    if response == win32con.IDYES:
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
            webbrowser.open("http://%s:%s/logout" % (DOMAIN, self.server_port))
    """
    pass

def main():
    menu_options = (
            ('Open Dashboard', None, open_dashboard),)
            #('Start Service', None, start_service),)
            #('Stop Service', None, stop_service),
            #('Reset Password', None, reset_password))

    icon = "icons/mycubevaulticon.ico"
    hover_text = 'MyCube Vault'

    st = SysTray(icon, hover_text, menu_options,
            on_quit=quit_services, default_menu_index=1)
    start_service(st)
    st.run()

if __name__ == "__main__":
    freeze_support()
    main()
