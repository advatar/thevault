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
import gtk
import gobject
import webbrowser
from multiprocessing import freeze_support
from systrayubuntu import SysTray
from myvault.helpers import pscan, is_online
from settings import HOST as DOMAIN, need_update

def get_path(target):
    path = os.path.dirname(os.path.realpath(__name__))
    if path.endswith('library.zip'):
        new_path = os.path.sep.join(path.split(os.path.sep)[:-1])
    else:
        new_path = os.path.sep.join(path.split(os.path.sep))
    return new_path

def start_service(self, widget, data=None):
    """
    Look for an open port then start the webservice on that port.
    """
    port = str(pscan())
    if not hasattr(self, 'server_pid') or self.server_pid is None:
        if re.search(r"python(.exe)?$", sys.executable):
            self.server_process = subprocess.Popen([sys.executable, 'server.py', port])
        else:
            if re.search(r".exe$", sys.executable):
                exe = 'server.exe'
            else:
                exe = 'server'
            #path = get_path(sys.executable)
            path = os.path.dirname(sys.executable)
            print "executable path %r" % path
            os.chdir(path)
            path = os.path.join(path, exe)
            self.server_process = subprocess.Popen([path, port])

        self.server_pid = self.server_process.pid
        self.server_host = DOMAIN
        self.server_port = port
    
    # let's open the browser
    time.sleep(2)
    webbrowser.open("http://%s:%s" % (DOMAIN, self.server_port))

def restart_service(self, widget, data=None):
    """
    Look for an open port then start the webservice on that port.
    """
    if hasattr(self, 'server_pid') and self.server_pid:
        try:
            try:
                urllib2.urlopen("http://%s:%s/stop" % ("127.0.0.1", self.server_port), timeout=1)
            except Exception, e:
                pass
            self.server_process.wait()
            self.server_pid = None
        except IOError, e:
            print "ignoring IOError %r" % e

    port = str(pscan())
    from settings import HOST as DOMAIN
    if not is_online():
        DOMAIN = "127.0.0.1"

    if not hasattr(self, 'server_pid') or self.server_pid is None:
        if re.search(r"python(.exe)?$", sys.executable):
            self.server_process = subprocess.Popen([sys.executable, 'server.py', port])
        else:
            if re.search(r".exe$", sys.executable):
                exe = 'server.exe'
            else:
                exe = 'server'
            #path = get_path(sys.executable)
            path = os.path.dirname(sys.executable)
            os.chdir(path)
            path = os.path.join(path, exe)
            self.server_process = subprocess.Popen([path, port])

        self.server_pid = self.server_process.pid
        self.server_port = port
        self.server_host = DOMAIN


def stop_service(self, widget, data=None):
    """
    Stop the webservice but not quit the program.
    """
    print "stopping service"
    if hasattr(self, 'server_pid') and self.server_pid:
        try:
            try:
                urllib2.urlopen("http://%s:%s/stop" % ("127.0.0.1", self.server_port), timeout=1)
            except Exception, e:
                print "%r" % e
            self.server_process.wait()
            self.server_pid = None
        except IOError, e:
            print "%r" % e

def open_dashboard(self, widget, data=None):
    if not hasattr(self, "server_port") or not self.server_port:
        return None
    webbrowser.open("http://%s:%s" % (DOMAIN, self.server_port))


def quit_services(self, widget, data=None):
    """
    Stop the webservice and quit the program.
    """
    print "quitting"
    if hasattr(self, 'server_pid') and self.server_pid:
        try:
            try:
                urllib2.urlopen("http://%s:%s/stop" % ("127.0.0.1", self.server_port), timeout=1)
            except Exception, e:
                pass
            self.server_process.wait()
            self.server_pid = None
        except IOError, e:
            print "%r" % e

    # give time to subprocess to cleanup itself
    time.sleep(2)
    self.quit(widget, data)
    
def reset_password(self, widget, data=None):
    """
    Reset user's password. Let them provide a new one on next access.
    """
    message = "This will reset your password. Are you sure?"
    dialog = gtk.MessageDialog(
        None,
        gtk.DIALOG_MODAL,
        gtk.MESSAGE_QUESTION,
        gtk.BUTTONS_YES_NO,
        message)
    response = dialog.run()
    dialog.destroy()
    
    if response == gtk.RESPONSE_YES:
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


def update_dialog(self, widget, data=None):
    message = """There is a new version available.
    Do you want to download?"""

    dialog = gtk.MessageDialog(
            None,
            gtk.DIALOG_MODAL,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_YES_NO,
            message)
    self.displayed = True
    response = dialog.run()
    dialog.destroy()

    if response == gtk.RESPONSE_YES:
        webbrowser.open("http://sourceforge.net/projects/themycubevault/files/MyCubeVault.exe/download")

def no_update_dialog(self, widget, data=None):
    message = "You are currently using the latest version."
    dialog = gtk.MessageDialog(
            None,
            gtk.DIALOG_MODAL,
            gtk.MESSAGE_INFO,
            gtk.BUTTONS_OK,
            message)
    self.displayed = True
    dialog.run()
    dialog.destroy()


def check_updates(self, widget, data=None):
    if need_update():
        update_dialog(self, widget)
    else:
        no_update_dialog(self, widget)


def main():
    menu_options = (
            ('Open Dashboard', open_dashboard),
            ('Check for updates', check_updates),
            #('Start Service', start_service),
            #('Stop Service', stop_service),
            #('Reset Password', reset_password),
            ('Quit', quit_services))

    icon_path = SysTray.get_path('icons')

    st = SysTray(menu_options, 'mycubevaulticon', icon_path)
    start_service(st, None)

    def connection_status(st):
        #stop_services(st, None)
        #print "checking connection status from launcher"
        if is_online():
            if st.server_host == "127.0.0.1":
                try:
                    restart_service(st, None)
                except Exception, e:
                    #print "%r" % e
                    pass
        else:
            if st.server_host != "127.0.0.1":
                try:
                    restart_service(st, None)
                except Exception, e:
                    #print "%r" % e
                    pass
        return True

   
    def callback(st):
        try:
            data = urllib2.urlopen("http://%s:%s/check_restart" % (st.server_host, st.server_port), timeout=2).read()
            if data == "true":
                restart_service(st, None)
        except Exception, e:
            pass
        return True

    def update_callback(st):
        if need_update():
            if hasattr(st, "displayed") and not st.displayed:
                update_dialog(st, None)

    gobject.timeout_add(3000, callback, st)
    gobject.timeout_add(3600 * 1000, update_callback, st)
    st.start()
    
if __name__ == "__main__":
    freeze_support()
    main()
