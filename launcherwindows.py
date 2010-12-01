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
import win32ui
from myvault.helpers import pscan, is_online
from settings import HOST, need_update

def start_service(self):
    """
    Look for an open port then start the webservice on that port.
    """
    port = str(pscan())
    if not hasattr(self, 'server_pid') or self.server_pid is None:
        start_server(self, port) 
    
    # let's open the browser
    time.sleep(2)
    webbrowser.open("http://%s:%s" % (HOST, self.server_port))

def start_server(self, port):
    if re.search(r"python.*$", sys.executable):
        self.server_process = subprocess.Popen([sys.executable, 'server.py', port],
                creationflags=win32con.CREATE_NEW_PROCESS_GROUP)
    else:
        path = os.path.dirname(sys.executable)
        server_path = os.path.join(path, 'server.exe')
        os.chdir(path)
        self.server_process = subprocess.Popen([server_path, port],
                creationflags=win32con.CREATE_NEW_PROCESS_GROUP)

    self.server_pid = self.server_process.pid
    self.server_port = port

def restart_service(self):
    if not hasattr(self, 'server_pid') or self.server_pid is None:
        start_server(self, self.server_port)
    else:
        try:
            urllib2.urlopen("http://%s:%s/stop" % (HOST, self.server_port), timeout=1)
        except Exception:
            pass

        self.server_process.wait()
        self.server_pid = None
        start_server(self, self.server_port)

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


def with_update_dialog(self):
    message = "A new version of MyCube Vault is available for download. Download update?"
    self.displayed = True
    response = win32ui.MessageBox(
            message,
            "MyCube Vault",
            win32con.MB_YESNO)
    if response == win32con.IDYES:
        webbrowser.open("http://sourceforge.net/projects/themycubevault/files/MyCubeVault.exe/download")



def without_update_dialog(self):
    message = "There is no updated version of MyCube Vault yet. Try again next time."
    self.displayed = True
    win32ui.MessageBox(
            message,
            "MyCube Vault",
            win32con.MB_OK)

def check_updates(self):
    if need_update():
        with_update_dialog(self)
    else:
        without_update_dialog(self)

def main():
    menu_options = (
            ('Open Dashboard', None, open_dashboard),
            ('Check for updates', None, check_updates),)
            #('Start Service', None, start_service),)
            #('Stop Service', None, stop_service),
            #('Reset Password', None, reset_password))

    icon = "icons/mycubevaulticon.ico"
    hover_text = 'MyCube Vault'

    st = SysTray(icon, hover_text, menu_options,
            on_quit=quit_services, default_menu_index=1)
    start_service(st)

    import timer
    def callback(timer_id, timer_t):
        try:
            data = urllib2.urlopen("http://%s:%s/check_restart" % (HOST, st.server_port), timeout=2).read()
            if data == "true":
                restart_service(st)
        except Exception:
            pass

    def update_monitor(timer_id, timer_t):
        if need_update():
            if not (hasattr(st, 'displayed') and st.displayed):
                with_update_dialog(st)
            else:
                if hasattr(st, 'update_timer'):
                    timer.kill_timer(st.update_timer)
                    st.update_timer = None

    timer.set_timer(3000, callback)
    st.update_timer = timer.set_timer(7200 * 1000, update_monitor)
    st.run()

if __name__ == "__main__":
    freeze_support()
    main()

# vim: set et sts=4 ts=4 sw=4:
