import Crypto
reload(Crypto)
from Crypto.PublicKey import RSA
from Crypto import Random

import pdb
import pygtk
pygtk.require('2.0')
import gtk

import smtplib
import mimetypes
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEAudio import MIMEAudio
from email.MIMEImage import MIMEImage
from email.Encoders import encode_base64


def load_key(rsa_path):
    key = Crypto.PublicKey.RSA.importKey(open(rsa_path, 'r').read())
    return key


def encrypt_and_save(key, text, filename):
    pub_key = key.publickey()
    data = pub_key.encrypt(text,32)

    f = open(filename,'wb')
    f.write(data[0])
    f.close()


def read_file_contents(filepath):
    f = open(filepath,'rb')
    data = f.read()
    f.close()
    return data
    
import os
home_dir = os.path.expanduser('~')
key_path = os.path.join(home_dir, 'headache_diary.pkl')
key = load_key(key_path)
ryan_pw_encoded = read_file_contents(os.path.join(home_dir, 'junk_ryan.txt'))
missy_pw_encoded = read_file_contents(os.path.join(home_dir, 'junk_missy.txt'))
missy_email_encoded = read_file_contents(os.path.join(home_dir, 'm_address.txt'))

ryan_pw = key.decrypt(ryan_pw_encoded)
missy_pw = key.decrypt(missy_pw_encoded)
missy_email = key.decrypt(missy_email_encoded)

import time
now = time.localtime()
hd_title = time.strftime('%m_%d_%y headache diary %H:%M %p', now)

notebook_title = time.strftime('%m_%Y', now)

box_defaults = (False, False, 5)

def sendMail(recipients, subject, text, username, password, \
             *attachmentFilePaths):
    if type(recipients) == str:
        recipients = [recipients]

    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    for attachmentFilePath in attachmentFilePaths:
        msg.attach(getAttachment(attachmentFilePath))

    mailServer = smtplib.SMTP('smtp.gmail.com', 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(username, password)
    mailServer.sendmail(username, recipients, msg.as_string())
    mailServer.close()


class headache_diary_gui(object):
    def delete(self, widget, event=None):
        gtk.main_quit()
        return False


    def send_to_evernote(self, widget, data=None):
        subject, body = self.compose_email()
        sendMail(missy_email, subject, body, \
                 'missykrauss@gmail.com', missy_pw)
        self.delete(self.window)


    def set_tags(self):
        tag_str = ''
        if 5 < now.tm_hour < 12:
            tag_str += 'morning'
        elif 18 < now.tm_hour < 24:
            tag_str += 'evening'
        self.tags_entry.set_text(tag_str)
        
        
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.connect("delete_event", self.delete)
        window.set_border_width(10)
        self.window = window
        self.ag = gtk.AccelGroup()
        self.window.add_accel_group(self.ag)        

        main_vbox = gtk.VBox(homogeneous=False, spacing=1)

        title_label = gtk.Label('Title:')
        hbox0 = gtk.HBox(homogeneous=False)
        hbox0.pack_start(title_label,False)
        self.title_entry = gtk.Entry()
        hbox0.pack_start(self.title_entry)
        main_vbox.pack_start(hbox0,False)        
        #main_vbox.pack_start(self.title_entry,False)
        title_label.show()
        self.title_entry.set_text(hd_title)
        self.title_entry.set_position(-1)
        self.title_entry.show()

        pain_level_label = gtk.Label('Pain Level:')
        hbox1 = gtk.HBox(homogeneous=False)
        hbox1.pack_start(pain_level_label,False)
        self.pain_level_entry = gtk.Entry()
        hbox1.pack_start(self.pain_level_entry)
        main_vbox.pack_start(hbox1,False)        
        #main_vbox.pack_start(self.title_entry,False)
        pain_level_label.show()
        self.pain_level_entry.set_size_request(30,-1)
        self.pain_level_entry.set_text('')
        self.pain_level_entry.show()


        body_label = gtk.Label('Diary Entry Body:')
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
        title = 'Headache Diary GUI'
        self.window.set_title(title)
        # and the window
        #self.window.show()
        self.window.add(main_vbox)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.show_all()


    def compose_email(self):
        title = self.title_entry.get_text()

        pl_str = self.pain_level_entry.get_text()
        pl_f = float(pl_str)
        pl_i = int(pl_f)
        pl_tag = 'pl%i' % pl_i
        
        start = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        body_str = self.textbuffer.get_text(start,end)

        tags_str = self.tags_entry.get_text()
        tags_list = tags_str.split(',')
        clean_tags = [item.strip() for item in tags_list]
        all_tags = [pl_tag] + clean_tags
        tags_with_hash = ['#' + item for item in all_tags]
        subject_tag_str = ' '.join(tags_with_hash)

        subject = '%s @%s %s' % (title, notebook_title, subject_tag_str)
        
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

