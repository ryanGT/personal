#!/usr/bin/env python

# example helloworld.py
import os

import rwkmisc

settings_path = 'picture_importer_settings.pkl'

import pygtk
pygtk.require('2.0')
import gtk


def my_dir_chooser(pathin=None):
    dialog = gtk.FileChooserDialog("Open..",
                           None,
                           #gtk.FILE_CHOOSER_ACTION_SAVE,
                           gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,        
                           #gtk.FILE_CHOOSER_ACTION_OPEN,
                           (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                            gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        #gtk.STOCK_SAVE, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)
    if pathin is not None:
        dialog.set_current_folder(pathin)

    filter = gtk.FileFilter()
    filter.set_name("JPEG files")
    filter.add_pattern("*.jpg")
    dialog.add_filter(filter)

    filter = gtk.FileFilter()
    filter.set_name("All files")
    filter.add_pattern("*")
    dialog.add_filter(filter)


    response = dialog.run()
    out = None
    if response == gtk.RESPONSE_OK:
        out = dialog.get_filename()
    ## elif response == gtk.RESPONSE_CANCEL:
    ##     print 'Closed, no files selected'
    dialog.destroy()

    return out
    


class picture_importer(rwkmisc.gui_that_saves):
    # This is a callback function. The data arguments are ignored
    # in this example. More on callbacks below.
    def browse1(self, widget, data=None):
        startpath = None
        curpath = self.path1.get_text()
        print('curpath = ' + curpath)
        if curpath:
            startpath = curpath
        path = my_dir_chooser(startpath)
        if path is not None:
            self.path1.set_text(path)
        #chooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        

    def delete_event(self, widget, event, data=None):
        # If you return FALSE in the "delete_event" signal handler,
        # GTK will emit the "destroy" signal. Returning TRUE means
        # you don't want the window to be destroyed.
        # This is useful for popping up 'are you sure you want to quit?'
        # type dialogs.
        print "delete event occurred"

        # Change FALSE to TRUE and the main window will not be destroyed
        # with a "delete_event".
        return False

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        self.save(settings_path)
        gtk.main_quit()

    def __init__(self):
        # create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    
        # When the window is given the "delete_event" signal (this is given
        # by the window manager, usually by the "close" option, or on the
        # titlebar), we ask it to call the delete_event () function
        # as defined above. The data passed to the callback
        # function is NULL and is ignored in the callback function.
        self.window.connect("delete_event", self.delete_event)
    
        # Here we connect the "destroy" event to a signal handler.  
        # This event occurs when we call gtk_widget_destroy() on the window,
        # or if we return FALSE in the "delete_event" callback.
        self.window.connect("destroy", self.destroy)
    
        # Sets the border width of the window.
        self.window.set_border_width(10)
    
        # Creates a new button with the label "Hello World".
        self.button1 = gtk.Button("browse")
        self.path1 = gtk.Entry()
        entry_width = 400
        self.path1.set_size_request(entry_width,-1)
        # When the button receives the "clicked" signal, it will call the
        # function hello() passing it None as its argument.  The hello()
        # function is defined above.
        self.button1.connect("clicked", self.browse1, None)

        hbox1 = gtk.HBox(homogeneous=False)
        hbox1.pack_start(self.path1,False)
        hbox1.pack_start(self.button1,False)

        big_vbox = gtk.VBox(homogeneous=False)

        big_vbox.pack_start(hbox1,False)

        # This will cause the window to be destroyed by calling
        # gtk_widget_destroy(window) when "clicked".  Again, the destroy
        # signal could come from here, or the window manager.
        #self.button.connect_object("clicked", gtk.Widget.destroy, self.window)
    
        # This packs the button into the window (a GTK container).
        self.window.add(big_vbox)
    
        # The final step is to display this newly created widget.
        self.button1.show()
        self.path1.show()

        #I need to save and load values when getting and setting the
        #values requires different methods.  How do I do this in a
        #general and helpful way?
        self._initialize_saving()
        self.append_item('path1', self.path1.get_text, self.path1.set_text)

        if os.path.exists(settings_path):
            self.load(settings_path)
    
        # and the window
        #self.window.show()
        self.window.set_title('Picture Importer v. 1.0.0')
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.show_all()

    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()

# If the program is run directly or passed as an argument to the python
# interpreter then create a HelloWorld instance and show it
if __name__ == "__main__":
    myapp = picture_importer()
    myapp.main()
