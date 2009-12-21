from scipy import *
import spreadsheet, EXIF, csv
import os, time, md5sum
#import odict

from IPython.Debugger import Pdb

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
        'image_labels','ryan_rating','missy_rating', \
        'md5sum']

colmap = dict(zip(cols, cols))
    

def seconds_to_str(seconds):
    st = time.localtime(seconds)
    time_str = time.strftime(time_fmt, st)
    return time_str


empty_attrs = ['caption','image_labels','ryan_rating','missy_rating']

class photo(object):
    def read_EXIF_data(self):
        tags = EXIF.process_file_from_path(self.pathin)
        for key, attr in EXIF_map.iteritems():
            val = str(tags[key])
            setattr(self, attr, val)

    def get_os_data(self):
        self.mtime = seconds_to_str(os.path.getmtime(self.pathin))
        self.ctime = seconds_to_str(os.path.getctime(self.pathin))
        self.size = os.path.getsize(self.pathin)/1.0e6#convert to MB
        
    def find_relpath(self):
        self.basepath = None
        self.relpath = None
        for base in basepaths:
            if self.folder.find(base) == 0:
                self.basepath = base
                N = len(base)
                relpath = self.folder[N:]
                if (relpath[0] == '/') or (relpath[0] == '\\'):
                    relpath = relpath[1:]
                self.relpath = relpath
                break
                
    def __init__(self, pathin, get_EXIF_data=True, \
                 get_os_data=True, calc_md5=True, basepath=None):
        #t1 = time.time()
        self.pathin = pathin
        self.folder, self.filename = os.path.split(pathin)
        self.find_relpath()
        #t2 = time.time()
        if get_EXIF_data:
            self.read_EXIF_data()
        #t3 = time.time()
        if get_os_data:
            self.get_os_data()
        #t4 = time.time()
        if calc_md5:
            self.md5sum = md5sum.md5sum(self.pathin)
        #t5 = time.time()
        for attr in empty_attrs:
            setattr(self, attr, None)
        #t6 = time.time()
##         for i in range(2,7):
##             dt = 't%i-t%i' % (i, i-1)
##             exec('curt='+dt)
##             print(dt + '='+str(curt))

    def torow(self):
        rowout = None
        for attr in cols:
            val = getattr(self, attr)
            if val is None:
                val = ''
            if rowout is None:
                rowout = [val]
            else:
                rowout.append(val)
        return rowout
        
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
            for attr in cols:
                setattr(self, attr, [])

    def search_for_photo(self, photo):
        if photo.md5sum in self.md5sum:
            ind = self.md5sum.index(photo.md5sum)
            return ind
        
    def add_photo(self, photo, verbosity=1, copy=False):
        ind = self.search_for_photo(photo)
        if ind:
            if verbosity > 0:
                print('photo already in dB:')
                print('  md5sum: ' + str(photo.md5sum))
                print('  filename: ' + photo.filename)
                print('  db filename: ' + self.filename[ind])
        else:
            for attr in cols:
                val = getattr(photo, attr)
                vect = getattr(self, attr)
                vect.append(val)
            self.alldata.append(photo.torow())
                #setattr(self, attr, val)#shouldn't be necessary

    def add_photos(self, photo_list, *args, **kwargs):
        for photo in photo_list:
            self.add_photo(photo, *args, **kwargs)


    def save(self, pathout=None):
        if pathout is None:
            pathout = self.get_new_path()
        self.WriteAllDataCSV(pathout, append=False)
        

if __name__ == '__main__':
    import file_finder
    db_path = '/mnt/personal/pictures/Joshua_Ryan/photo_db.csv'
    mydb = photo_db(db_path)
#    folder = '/mnt/personal/pictures/Joshua_Ryan/2009/Dec_2009/Santa_Hat_Pictures/2009-12-17--12.48.31'
    folder = '/mnt/personal/pictures/Joshua_Ryan/2009/Dec_2009/Santa_Hat_Pictures/'
    image_finder = file_finder.Image_Finder(folder)
    #paths = image_finder.Find_All_Images()
    paths = image_finder.Find_Images()
    photos = [photo(path) for path in paths]
    mydb.add_photos(photos)
