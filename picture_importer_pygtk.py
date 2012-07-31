#!/usr/bin/env python

# example helloworld.py
import os

import rwkmisc

settings_path = 'picture_importer_settings.pkl'

import pygtk
pygtk.require('2.0')
import gtk
import gobject

import file_finder

import threading

import copy_based_on_EXIF_date as copy_lib

class copy_thread(threading.Thread):
    def __init__(self, GUI, source_path, dest_root):
        threading.Thread.__init__(self)
        self.GUI = GUI
        self.source_path = source_path
        self.dest_root = dest_root
        self.finder_all = file_finder.Multi_Media_Finder(source_path)
        movie_exts = ['.mov', '.mp4', '.avi']
        picture_exts = ['.jpg','.nef','.cr2']
        self.movie_finder = file_finder.Multi_Media_Finder(source_path, \
                                                           extlist=movie_exts)
        self.picture_finder = file_finder.Multi_Media_Finder(source_path, \
                                                             extlist=picture_exts)
        self.all_paths = self.finder_all.Find_All_Files()
        self.N = len(self.all_paths)

        
    def run(self):
        #in order to fascilitate finding the dates of movie files
        #based on neighboring stil pictures, you need to copy all
        #movie files first

        #but do you do this at the copy thread level or the GUI level?
        self.movie_paths = self.movie_finder.Find_All_Files()
        self.N_movies = len(self.movie_paths)
        gobject.idle_add(self.GUI.append_to_log, 'Found %i movie files' % self.N_movies)
                         
        self.picture_paths = self.picture_finder.Find_All_Files()
        self.N_pictures = len(self.picture_paths)
        gobject.idle_add(self.GUI.append_to_log, 'Found %i picture files' % self.N_pictures)

        if self.N_movies > 0:
            gobject.idle_add(self.GUI.append_to_log, 'Copying movie files')
        
        for i, curpath in enumerate(self.movie_paths):
            fraction = float(1.0+i)/self.N
            folder, filename = os.path.split(curpath)
            fno, ext = os.path.splitext(filename)
            gobject.idle_add(self.GUI.set_progress, fraction, filename)
            copy_lib.copy_one_movie_file(curpath, root=self.dest_root)

        gobject.idle_add(self.GUI.append_to_log, 'Copying picture files')

        for i, curpath in enumerate(self.picture_paths):
            fraction = float(i+self.N_movies)/self.N
            folder, filename = os.path.split(curpath)
            fno, ext = os.path.splitext(filename)
            gobject.idle_add(self.GUI.set_progress, fraction, filename)
            copy_lib.copy_one_image(curpath, root=self.dest_root)
            

        gobject.idle_add(self.GUI.append_to_log, 'Copying completed.')


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
    filter.set_name("All files")
    filter.add_pattern("*")
    dialog.add_filter(filter)

    filter = gtk.FileFilter()
    filter.set_name("JPEG files")
    filter.add_pattern("*.jpg")
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

    def browse2(self, widget, data=None):
        startpath = None
        curpath = self.path2.get_text()
        print('curpath = ' + curpath)
        if curpath:
            startpath = curpath
        path = my_dir_chooser(startpath)
        if path is not None:
            self.path2.set_text(path)
        #chooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)


    def set_progress(self, fraction, filename):
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(filename)
        

    def go(self, widget, data=None):
        source_path = self.path1.get_text()
        dest_root = self.path2.get_text()
        if not source_path:
            self.append_to_log('Cannot copy files without valid source path.')
            return
        if not os.path.exists(source_path):
            self.append_to_log('source path does not exist')
        if not os.path.exists(dest_root):
            self.append_to_log('destination root does not exist:')
            self.append_to_log(dest_root)

        my_thread = copy_thread(self, source_path, dest_root)
        my_thread.start()
        
    def append_to_log(self, msg, scroll=True):
        if msg == '':
            msg = '\n'
        elif msg[-1] != '\n':
            msg += '\n'
        end_iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end_iter, msg)

        if scroll:
            #mark = self.textbuffer.get_insert()
            #self.textview.scroll_to_mark(mark, 0.01)
            #end_iter = self.textbuffer.get_end_iter()
            #mymark = self.textbuffer.create_mark("mymark", end_iter, False)
            #self.textview.scroll_to_mark(mymark, 0.45)
            #self.textview.scroll_to_iter(end_iter, 0.01)
            #self.textview.scroll_mark_onscreen(self.textbuffer.get_insert())
            #self.textview.scroll_to_mark(self.textbuffer.get_insert(), 0)
            adj = self.text_scrollw.get_vadjustment()
            adj.set_value( adj.upper )# - adj.pagesize )


    def clear_log(self):
        start_iter = self.textbuffer.get_start_iter()
        end_iter = self.textbuffer.get_end_iter()
        self.textbuffer.delete(start_iter, end_iter)


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

        #dest browser
        self.button2 = gtk.Button("browse")
        self.path2 = gtk.Entry()
        self.path2.set_size_request(entry_width,-1)
        # When the button receives the "clicked" signal, it will call the
        # function hello() passing it None as its argument.  The hello()
        # function is defined above.
        self.button2.connect("clicked", self.browse2, None)


        # Creates a new button with the label "Hello World".
        self.go_button = gtk.Button("Copy files")
        self.go_button.connect("clicked", self.go, None)        


        #packing the gui boxes
        big_vbox = gtk.VBox(homogeneous=False)

        #source label
        source_label = gtk.Label('Source Directory')
        hbox0 = gtk.HBox(homogeneous=False)
        hbox0.pack_start(source_label,False)
        big_vbox.pack_start(hbox0,False)

        #source browser
        hbox1 = gtk.HBox(homogeneous=False)
        hbox1.pack_start(self.path1,False)
        hbox1.pack_start(self.button1,False)
        big_vbox.pack_start(hbox1,False)
        
        #empty string spacer
        spacer_label = gtk.Label('')
        hbox2 = gtk.HBox(homogeneous=False)
        hbox2.pack_start(spacer_label,False)
        big_vbox.pack_start(hbox2,False)

        #dest label
        dest_label = gtk.Label('Destination Root Directory')
        hbox3 = gtk.HBox(homogeneous=False)
        hbox3.pack_start(dest_label,False)
        big_vbox.pack_start(hbox3,False)

        #dest browser
        hbox4 = gtk.HBox(homogeneous=False)
        hbox4.pack_start(self.path2,False)
        hbox4.pack_start(self.button2,False)
        big_vbox.pack_start(hbox4,False)

        #empty string spacer
        spacer_label = gtk.Label('')
        hbox5 = gtk.HBox(homogeneous=False)
        hbox5.pack_start(spacer_label,False)
        big_vbox.pack_start(hbox5,False)

        #go button
        hbox6 = gtk.HBox(homogeneous=False)
        hbox6.pack_start(self.go_button,False)
        big_vbox.pack_start(hbox6,False)


        #empty string spacer
        spacer_label = gtk.Label('')
        hbox7 = gtk.HBox(homogeneous=False)
        hbox7.pack_start(spacer_label,False)
        big_vbox.pack_start(hbox7,False)

        #progress label
        progress_label = gtk.Label('Progress')
        hbox8 = gtk.HBox(homogeneous=False)
        hbox8.pack_start(progress_label,False)
        big_vbox.pack_start(hbox8,False)


        #progress bar
        self.progress_bar = gtk.ProgressBar()
        hbox9 = gtk.HBox(homogeneous=False)
        hbox9.pack_start(self.progress_bar,False)
        self.progress_bar.set_size_request(entry_width,25)
        big_vbox.pack_start(hbox9,False)

        
        #empty string spacer
        spacer_label = gtk.Label('')
        hbox10 = gtk.HBox(homogeneous=False)
        hbox10.pack_start(spacer_label,False)
        big_vbox.pack_start(hbox10,False)


        #log label
        log_label = gtk.Label('Log')
        hbox11 = gtk.HBox(homogeneous=False)
        hbox11.pack_start(log_label,False)
        big_vbox.pack_start(hbox11,False, False, 5)

        
        #log text thingy
        self.textview = gtk.TextView()
        self.textbuffer = self.textview.get_buffer()

        self.textbuffer.set_text("")

        w = 500
        h = 100
        self.textview.set_size_request(w,h)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(0)
        big_vbox.pack_start(scrolled_window, False, False, 0)
        scrolled_window.set_size_request(w,h)

        scrolled_window.show()

        scrolled_window.add_with_viewport(self.textview)
        self.text_scrollw = scrolled_window
        self.textview.show()

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
        self.append_item('path2', self.path2.get_text, self.path2.set_text)

        if os.path.exists(settings_path):
            self.load(settings_path)


        source_path = self.path1.get_text()
        if source_path:
            if os.path.exists(source_path):
                myfinder = file_finder.Multi_Media_Finder(source_path)
                files = myfinder.Find_Top_Level_Files()
                self.append_to_log('Found %i image and movie files in %s.' % \
                                   (len(files), source_path))
                
        # and the window
        #self.window.show()
        self.window.set_title('Picture Importer v. 1.0.0')
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.show_all()

    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()


###################################################
###################################################

#To do:

# 1. I need a "Go" button and a method to actually move the files
# 2. I need a progress bar widget for copying
# 3. I need to check the status of the source directory beforing clicking Go
#
#    - does the source directory exist
#    - how many pictures or movies are in the source directory
#    - if the source is a memory card, are there pictures in
#      other folders that that would be reasonable to import?
#
#      - does the path start with /media?

# 4. I need to handle the exif date of raw photos and movies,
#    possibly using neiboring file #'s

###################################################
###################################################

# If the program is run directly or passed as an argument to the python
# interpreter then create a HelloWorld instance and show it
if __name__ == "__main__":
    myapp = picture_importer()
    gtk.gdk.threads_init()
    myapp.main()
