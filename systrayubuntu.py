import gobject
import gtk
import appindicator
import os

class SysTray(object):
    
    def __init__(self, menus, icon='indicator-messages-new', icon_path=None):
        indicator = appindicator.Indicator(
            'myvault-indicator',
            'indicator-messages',
            appindicator.CATEGORY_OTHER,
            icon_path)
        indicator.set_status(appindicator.STATUS_ACTIVE)
        indicator.set_icon(icon)
        
        menu = gtk.Menu()
        
        for title, action in menus:
            menuitem = gtk.MenuItem(title)
            setattr(self.__class__, action.__name__, action)
            menuitem.connect('activate', getattr(self, action.__name__))
            menu.append(menuitem)
            menuitem.show()
            
        # menuitem = gtk.MenuItem('Quit')
        # menuitem.connect('activate', self.quit)
        # menu.append(menuitem)
        # menuitem.show()
        
        indicator.set_menu(menu)
        self.indicator = indicator
    
    @classmethod
    def get_path(self, target):
        path = os.path.dirname(os.path.realpath(__file__))
        if path.endswith('library.zip'):
            return os.path.sep.join(path.split(os.path.sep)[:-1] + [target])
        else:
            return os.path.sep.join(path.split(os.path.sep) + [target])
    
    def start(self):
        gtk.main()

    def quit(self, widget, data=None):
        gtk.main_quit()
    

def open_dashboard(self, widget, data=None):
    print "open dashboard"
    print "%r" % self
    print "%r" % widget
    
def start_service(self, widget, data=None):
    print "start service"
    
def stop_service(self, widget, data=None):
    print "stop service"


def quit_services(self, widget, data=None):
    gtk.main_quit()

if __name__ == "__main__":
    
    menu_options = (
            ('Open Dashboard', open_dashboard),
            ('Start Service', start_service),
            ('Stop Service', stop_service),
            ('Quit', quit_services))

    icon = SysTray.get_path('systrayicon')

    st = SysTray(icon, menu_options)
    gtk.main()
    
