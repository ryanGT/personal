import os
import gmail_smtp

home_dir = os.path.expanduser('~')
missy_path = os.path.join(home_dir, 'm_address.txt')
ryan_path = os.path.join(home_dir, 'r_enote.txt')

missy_email = gmail_smtp.decrypt_from_file(missy_path)
ryan_email = gmail_smtp.decrypt_from_file(ryan_path)


class evernote_emailer(object):
    """This class sends emails to evernote from my gmail account."""
    def __init__(self, notebook_title, enote_email):
        self.notebook_title = notebook_title
        self.enote_email = enote_email

        
    def send_to_evernote(self, subject=None, tags=None):
        subject_out, body_out = self.compose_email(subject=subject, tags=tags)
        gmail_smtp.send_mail_gmail(self.enote_email, subject_out, \
                                   body_out, \
                                   attachmentFilePaths=[])


    def cleanup_tags(self, tags=None):
        if tags is None:
            tags = self.tags
        clean_tags = [item.strip() for item in tags]
        self.clean_tags = clean_tags
        return self.clean_tags
        

    def add_hashs_to_tags(self):
        tags_with_hash = ['#' + item for item in self.clean_tags]
        self.tags_with_hash = tags_with_hash
        return self.tags_with_hash


    def compose_email(self, subject=None, tags=None, body_str=''):
        self.cleanup_tags(tags)
        self.add_hashs_to_tags()
        subject_tag_str = ' '.join(self.tags_with_hash)

        subject = '%s @%s %s' % (subject, self.notebook_title, \
                                 subject_tag_str)
        return subject, body_str


class evernote_emailer_missy(evernote_emailer):
    """This class sends emails to evernote from my gmail account."""
    def __init__(self, notebook_title):
        missy_email
        self.notebook_title = notebook_title
        self.enote_email = missy_email


class evernote_emailer_ryan(evernote_emailer):
    """This class sends emails to evernote from my gmail account."""
    def __init__(self, notebook_title):
        missy_email
        self.notebook_title = notebook_title
        self.enote_email = ryan_email

