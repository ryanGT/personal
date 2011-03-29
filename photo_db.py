from scipy import *
import numpy
import spreadsheet, EXIF, csv
import os, time, md5sum, re, glob
from PIL import Image
#import odict

from IPython.Debugger import Pdb

time_fmt = '%Y:%m:%d %H:%M:%S'
stamp_fmt = '%m_%d_%y__%H_%M_%S'

def time_stamp_to_seconds(stampstr):
    st = time.strptime(stampstr, stamp_fmt)
    seconds = time.mktime(st)
    return seconds

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
        'exif_width', 'exif_height', 'PIL_width', \
        'PIL_height', 'caption', \
        'tags','rating',\
        'md5sum']

colmap = dict(zip(cols, cols))

def mysearch(arrayin, element):
    bool_vect = where(arrayin==element)[0]
    assert(len(bool_vect)==1), 'Did not find exactly 1 match for ' + str(element)
    return bool_vect[0]

def seconds_to_str(seconds):
    st = time.localtime(seconds)
    time_str = time.strftime(time_fmt, st)
    return time_str


empty_attrs = ['caption','tags','rating']

class photo(object):
    def read_EXIF_data(self):
        tags = EXIF.process_file_from_path(self.pathin)
        for key, attr in EXIF_map.iteritems():
            val = str(tags[key])
            setattr(self, attr, val)

    def get_PIL_size(self):
        img = Image.open(self.pathin)
        self.PIL_width, self.PIL_height = img.size
        

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
                 get_os_data=True, calc_md5=True, \
                 get_PIL_size=True, basepath=None):
        t1 = time.time()
        self.pathin = pathin
        self.folder, self.filename = os.path.split(pathin)
        self.find_relpath()
        t2 = time.time()
        if get_EXIF_data:
            self.read_EXIF_data()
        t3 = time.time()
        if get_os_data:
            self.get_os_data()
        t4 = time.time()    
        if get_PIL_size:
            self.get_PIL_size()
        t5 = time.time()
        if calc_md5:
            self.md5sum = md5sum.md5sum(self.pathin)
        t6 = time.time()
        for attr in empty_attrs:
            setattr(self, attr, None)
        t7 = time.time()
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
        if os.path.isdir(pathin):
            self.folder = pathin
            pathin = self.find_latest_db()
            self.namein = None
        else:
            self.folder, self.namein = os.path.split(pathin)
            
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
            if type(self.md5sum) == numpy.ndarray:
                ind = self.md5sum.tolist().index(photo.md5sum)
##                 t1 = time.time()
##                 index1 = where(self.md5sum==photo.md5sum)[0][0]
##                 t2 = time.time()
##                 index2 = mysearch(self.md5sum, photo.md5sum)
##                 t3 = time.time()
##                 index3 = self.md5sum.tolist().index(photo.md5sum)
##                 t4 = time.time()
##                 for i in range(2,5):
##                     dt = 't%i-t%i' % (i, i-1)
##                     exec('curt='+dt)
##                     print(dt + '='+str(curt))
##                 assert index1==index2, 'indices dont match'
##                 assert index1==index3, 'indices dont match'
##                 ind = index1
            else:
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
                if type(vect) == numpy.ndarray:
                    vect = numpy.append(vect, val)
                else:
                    vect.append(val)
            self.alldata.append(photo.torow())
                #setattr(self, attr, val)#shouldn't be necessary

    def add_photos(self, photo_list, *args, **kwargs):
        for photo in photo_list:
            self.add_photo(photo, *args, **kwargs)


    def find_latest_db(self, pat='photo_db_'):
        glob_pat = pat +'*.csv'
        csvpaths = glob.glob(os.path.join(self.folder, glob_pat))
        p = re.compile(pat+'(.*)\\.csv')
        stamps = []
        for csvpath in csvpaths:
            q = p.search(csvpath)
            stamp = q.group(1)
            stamps.append(stamp)
        seconds = map(time_stamp_to_seconds, stamps)
        ind = numpy.argmax(seconds)
        return csvpaths[ind]
            

        
    def get_new_path(self, basename='photo_db'):
        st = time.localtime()
        time_str = time.strftime(stamp_fmt, st)
        if basename[-1] != '_':
            basename += '_'
        self.csvname = basename + time_str + '.csv'
        self.csvpath = os.path.join(self.folder, self.csvname)
        return self.csvpath
        
        
    def save(self, pathout=None):
        if pathout is None:
            pathout = self.get_new_path()
        self.WriteAllDataCSV(pathout, append=False)
        

if __name__ == '__main__':
    import file_finder
    db_path = '/mnt/personal/pictures/Joshua_Ryan/'#photo_db_12_21_09__19_35_11.csv'
    mydb = photo_db(db_path)
#    folder = '/mnt/personal/pictures/Joshua_Ryan/2009/Dec_2009/Santa_Hat_Pictures/2009-12-17--12.48.31'
    folder = '/mnt/personal/pictures/Joshua_Ryan/2009/Dec_2009/Santa_Hat_Pictures/'
    image_finder = file_finder.Image_Finder(folder)
    #paths = image_finder.Find_All_Images()
    paths = image_finder.Find_Images()
    photos = [photo(path) for path in paths]
    mydb.add_photos(photos)
    mydb.save()
