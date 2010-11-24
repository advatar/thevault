# -*- coding: utf-8 -*-

import objc
from Foundation import *
from AppKit import *
from PyObjCTools import NibClassBuilder, AppHelper
import time
import sys

class Backup(NSObject):
    statusbar = None
    status_images = {'init':'icons/systrayicon.png'}
    images = {}
    
    def applicationDidFinishLaunching_(self, notification):
        pass
        
    def initWithMenus(self, menus):
        self = super(self.__class__, self).init()
        
        statusbar = NSStatusBar.systemStatusBar()
 
        self.statusitem = statusbar.statusItemWithLength_(NSVariableStatusItemLength)
        #self.statusitem.setHighlightMode_(1)
        self.statusitem.setToolTip_('MyVault')
        self.statusitem.setEnabled_(YES)

        # to signal what is going on 
        for i in self.status_images.keys():
          self.images[i] = NSImage.alloc().initByReferencingFile_(self.status_images[i])
          
        # Set initial image
        self.statusitem.setImage_(self.images['init'])
        #self.statusitem.setAlternateImage_(self.icons['clicked'])
          
        self.menu = NSMenu.alloc().init()
        self.menu.setDelegate_(self)
        #self.menu.setAutoenablesItems_(NO)

        for m_item, m_sel in menus:
            objc.classAddMethods(Backup, [m_sel])
            menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(*m_item)
            self.menu.addItem_(menuitem)
                            
        self.statusitem.setMenu_(self.menu)
        return self

    def applicationShouldTerminate_(self, notification):
        """
        Put cleanup routine here.
        """
        #print time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())
        return YES
    
    def validateMenuItem_(self, menuitem):
        if menuitem.performSelector_('title') in self.disabled_menuitems:
            return NO
        return YES

def startServer_(self, notification):
    print "starting server"
    
def stopServer_(self, notification):
    print "stopping server"
    
def quitApp_(self, notification):
    print "quitting"
    NSApp().terminate_(self)
    
if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    menus = [
        (('Start', 'startServer:', ''), startServer_),
        (('Stop', 'stopServer:', ''), stopServer_),
        (('Quit', 'quitApp:', ''), quitApp_),
    ]
    delegate = Backup.alloc().initWithMenus(menus)
        
    app.setDelegate_(delegate)
    
    AppHelper.runEventLoop()
