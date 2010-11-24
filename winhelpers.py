# -*- coding: utf-8 -*-
"""
Miscellaneous windows function
"""
import sys
if sys.platform == "win32":
    from win32com.client import Dispatch

def get_user_folders():
    """
    get all user's shell folder.
    http://win32com.goermezer.de/content/view/221/284/
    """
    import _winreg
    shell_folders = {}
    try:
        registry = _winreg.ConnectRegistry(
                None,
                _winreg.HKEY_CURRENT_USER)
    except WindowsError, e:
        print "%r" % e
        return shell_folders()

    try:
        reg_key = _winreg.OpenKey(
                registry,
                "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
    except WindowsError, e:
        print "%r" % e
        _winreg.CloseKey(registry)
        return shell_folders

    try:
        for i in range(0, _winreg.QueryInfoKey(reg_key)[1]):
            name, value, val_type = _winreg.EnumValue(reg_key, i)
            shell_folders[name] = value
        _winreg.CloseKey(reg_key)
        _winreg.CloseKey(registry)
        return shell_folders
    except WindowsError, e:
        print "%r" % e
        _winreg.CloseKey(reg_key)
        _winreg.CloseKey(registry)
        return {}
# http://www.blog.pythonlibrary.org/2010/01/23/using-python-to-create-shortcuts/
def create_shortcut(path, target='', wDir='', icon=''):
    ext = path[-3:]
    if ext == "url":
        shortcut = file(path, "w")
        shortcut.write('[InternetShortcut]\n')
        shortcut.write('URL=%s' % target)
        shortcut.close()
    else:
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = wDir
        if icon == '':
            pass
        else:
            shortcut.IconLocation = icon
        shortcut.save()

# vim: set et sts=4 ts=4 sw=4:
