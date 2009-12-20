from scipy import *
import spreadsheet, EXIF
import os, time
#import odict

time_fmt = '%Y:%m:%d %H:%M:%S'

#make sure the more specific paths are higher in the list since
#find_relpath will stop at the first match
basepaths = ['/mnt/personal/pictures/Joshua_Ryan/', \
             '/mnt/personal/pictures/']

EXIF_map = {'EXIF ExifImageWidth':'exif_width', \
            'EXIF ExifImageLength':'exif_height', \
            'EXIF DateTimeOriginal':'exif_date', \
            'EXIF DateTimeDigitized':'exif_date_digitized'
            }

## col_map = odict.OrderedDict([('filename','filename'), \
##                              ('relpath','relpath'), \
##                              ])

cols = ['filename','relpath','exif_date', \
        'exif_date_digitized', 'mtime', \
        'ctime', 'size', \
        'exif_width', 'exif_height', 'caption', \
        'labels','ryan_rating','missy_rating']

colmap = dict(zip(cols, cols))
    

def seconds_to_str(seconds):
    st = time.localtime(seconds)
    time_str = time.strftime(time_fmt, st)
    return time_str


empty_attrs = ['caption','labels','ryan_rating','missy_rating']

class photo(object):
    def read_EXIF_data(self):
        tags = EXIF.process_file_from_path(self.pathin)
        for key, attr in EXIF_map.iteritems():
            val = str(tags[key])
            setattr(self, attr, val)

    def get_os_data(self):
        self.mtime = seconds_to_str(os.path.getmtime(self.pathin))
        self.ctime = seconds_to_str(os.path.getctime(self.pathin))
        self.size = seconds_to_str(os.path.getsize(self.pathin))
        
    def find_relpath(self):
        self.basepath = None
        self.relpath = None
        for base in basepaths:
            if self.folder.find(base) == 0:
                self.basepath = base
                N = len(base)
                relpath = self.pathin[N:]
                if (relpath[0] == '/') or (relpath[0] == '\\'):
                    relpath = relpath[1:]
                self.relpath = relpath
                break
                
    def __init__(self, pathin, get_EXIF_data=True, \
                 get_os_data=True, basepath=None):
        self.pathin = pathin
        self.folder, self.filename = os.path.split(pathin)
        self.find_relpath()
        if get_EXIF_data:
            self.read_EXIF_data()
        if get_os_data:
            self.get_os_data()
        for attr in empty_attrs:
            setattr(self, attr, None)
        
        
class photo_db(spreadsheet.CSVSpreadSheet):
    def __init__(self, pathin, *args, **kwargs):
        spreadsheet.CSVSpreadSheet.__init__(self, pathin, *args, \
                                            **kwargs)
        self.colmap = colmap
        if os.path.exists(pathin):
            self.FindLabelRow('filename')
            self.FindDataColumns()
            self.MapCols()
        else:
            self.labels = cols


if __name__ == '__main__':
    db_path = '/mnt/personal/pictures/Joshua_Ryan/photo_db.csv'
    mydb = photo_db(db_path)
    image_finder = 
    #paths =
    #photos = [photo(path) for path in paths]
    #mydb.add_photos(photos)
