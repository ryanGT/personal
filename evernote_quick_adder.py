import pdb
import pygtk
pygtk.require('2.0')
import gtk

import time

import gmail_smtp

def make_date_time_title(titlein):
    now = time.localtime()
    pat = '%m_%d_%y ' + titlein + ' %H:%M %p'
    my_title = time.strftime(pat, now)
    return my_title

def make_month_year_name():
    my_title = time.strftime('%m_%Y', now)
    return my_title


box_defaults = (False, False, 5)

## def sendMail(recipients, subject, text, username, password, \
##              *attachmentFilePaths):

class evernote_gui(object):
    def delete(self, widget, event=None):
        gtk.main_quit()
        return False


    def send_to_evernote(self, widget, data=None):
        subject, body = self.compose_email()
        gmail_smtp.send_mail(self.enote_email, subject, body, \
                             self.gmail_username, self.gmail_pw)
        self.delete(self.window)


    def set_tags(self):
        """auto-set initial tags"""
        pass
        ## tag_str = ''
        ## if 5 < now.tm_hour < 12:
        ##     tag_str += 'morning'
        ## elif 18 < now.tm_hour < 24:
        ##     tag_str += 'evening'
        ## self.tags_entry.set_text(tag_str)


    def add_widgets_above(self):
        """This method would add widgets above the main entry box"""
        pass


    def set_initial_title(self):
        self.title_entry.set_text('')
        
        
    def __init__(self, notebook_title, enote_email, \
                 gmail_username, gmail_pw):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.connect("delete_event", self.delete)
        window.set_border_width(10)
        self.window = window
        self.ag = gtk.AccelGroup()
        self.window.add_accel_group(self.ag)

        self.notebook_title = notebook_title
        self.enote_email = enote_email
        self.gmail_username = gmail_username
        self.gmail_pw = gmail_pw

        main_vbox = gtk.VBox(homogeneous=False, spacing=1)
        self.main_vbox = main_vbox

        title_label = gtk.Label('Title:')
        hbox0 = gtk.HBox(homogeneous=False)
        hbox0.pack_start(title_label,False)
        self.title_entry = gtk.Entry()
        hbox0.pack_start(self.title_entry)
        main_vbox.pack_start(hbox0,False)        
        #main_vbox.pack_start(self.title_entry,False)
        title_label.show()
        self.set_initial_title()
        self.title_entry.set_position(-1)
        self.title_entry.show()

        self.add_widgets_above()


        body_label = gtk.Label('Note Body:')
        hbox2 = gtk.HBox(homogeneous=False)
        hbox2.pack_start(body_label,False)
        main_vbox.pack_start(hbox2,False)
        
        self.textview = gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
        self.textview.set_size_request(-1,150)

        main_vbox.pack_start(self.textview,False)        


        tags_label = gtk.Label('Tags:')
        hbox1 = gtk.HBox(homogeneous=False)
        hbox1.pack_start(tags_label,False)
        self.tags_entry = gtk.Entry()
        hbox1.pack_start(self.tags_entry)
        main_vbox.pack_start(hbox1,False)        
        #main_vbox.pack_start(self.title_entry,False)
        tags_label.show()
        self.tags_entry.set_size_request(30,-1)
        #self.tags_entry.set_text('')

        self.set_tags()
        
        self.tags_entry.show()


        self.send_button = gtk.Button("Send to Evernote")
        self.send_button.connect("clicked", self.send_to_evernote, None)
        hbox3 = gtk.HBox(homogeneous=False)
        hbox3.pack_end(self.send_button,*box_defaults)
        main_vbox.pack_start(hbox3,False)

        self.window.set_size_request(400,300)
        title = 'Notebook: ' + self.notebook_title
        self.window.set_title(title)
        # and the window
        #self.window.show()
        self.window.add(main_vbox)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.show_all()


    def get_tags_without_hash(self):
        tags_str = self.tags_entry.get_text()
        tags_list = tags_str.split(',')
        clean_tags = [item.strip() for item in tags_list]
        self.clean_tags = clean_tags
        return self.clean_tags


    def add_hashs_to_tags(self):
        tags_with_hash = ['#' + item for item in self.clean_tags]
        self.tags_with_hash = tags_with_hash
        return self.tags_with_hash


    def compose_email(self):
        title = self.title_entry.get_text()

        start = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        body_str = self.textbuffer.get_text(start,end)

        self.get_tags_without_hash()
        self.add_hashs_to_tags()
        subject_tag_str = ' '.join(self.tags_with_hash)

        subject = '%s @%s %s' % (title, self.notebook_title, \
                                 subject_tag_str)
        
        return subject, body_str


    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()

# If the program is run directly or passed as an argument to the python
# interpreter then create a HelloWorld instance and show it
if __name__ == "__main__":
    myapp = headache_diary_gui()
    #myapp.window.resize(400,300)
    #gtk.gdk.threads_init()
    myapp.main()

