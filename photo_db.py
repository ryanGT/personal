from scipy import *
import numpy
import spreadsheet, EXIF, csv
import os, time, md5sum, re, glob, pdb
from PIL import Image
#import odict

from IPython.Debugger import Pdb

time_fmt = '%Y:%m:%d %H:%M:%S'
stamp_fmt = '%m_%d_%y__%H_%M_%S'

import copy

def time_stamp_to_seconds(stampstr):
    st = time.strptime(stampstr, stamp_fmt)
    seconds = time.mktime(st)
    return seconds

def time_to_seconds2(time_str):
    st = time.strptime(time_str, time_fmt)
    seconds = time.mktime(st)
    return seconds


def find_earliest(time_str1, time_str2):
    seconds1 = time_to_seconds2(time_str1)
    seconds2 = time_to_seconds2(time_str2)
    if seconds1 < seconds2:
        return time_str1
    else:
        return time_str2
    

#make sure the more specific paths are higher in the list since
#find_relpath will stop at the first match
basepaths = ['/mnt/personal/pictures/Joshua_Ryan/', \
             '/mnt/personal/pictures/', \
             '/home/ryan/Pictures/']

EXIF_map = {'EXIF ExifImageWidth':'exif_width', \
            'EXIF ExifImageLength':'exif_height', \
            'EXIF DateTimeOriginal':'exif_date', \
            'EXIF DateTimeDigitized':'exif_date_digitized'
            }

## col_map = odict.OrderedDict([('filename','filename'), \
##                              ('relpath','relpath'), \
##                              ])

cols = ['photo_id','filename','relpath','folder_name', \
        'exif_date', 'exif_date_digitized', \
        'year','month','day','hour', 'minute', \
        'mtime', \
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

month_map = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', \
             5:'May', 6:'June', 7:'July', 8:'Aug', \
             9:'Sept', 10:'Oct', 11:'Nov', 12:'Dec'}

#need to be able to create a photo from a row cut from a photo_db for
#the deleted db.

class photo(object):
    def EXIF_date_to_attrs(self):
        try:
            struct = time.strptime(self.exif_date, time_fmt)
        except ValueError:
            print('EXIF problem for %s' % self.pathin)
            #Pdb().set_trace()
            os_str = find_earliest(self.mtime, self.ctime)
            print('using OS date/time: %s' % os_str)
            struct = time.strptime(os_str, time_fmt)
        self.year = struct.tm_year
        self.month = month_map[struct.tm_mon]
        self.day = struct.tm_mday
        self.hour = struct.tm_hour
        self.minute = struct.tm_min

        
    def read_EXIF_data(self):
        tags = EXIF.process_file_from_path(self.pathin)
        for key, attr in EXIF_map.iteritems():
            if tags.has_key(key):
                val = str(tags[key])
            else:
                val = ""
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
                junk, folder = os.path.split(relpath)
                self.folder_name = folder
                break

                
    def __init__(self, pathin=None, get_EXIF_data=True, \
                 get_os_data=True, calc_md5=True, \
                 get_PIL_size=True, basepath=None, dictin=None):
        if dictin is not None:
            for key, value in dictin.iteritems():
                setattr(self, key, value)
        else:
            #t1 = time.time()
            self.pathin = pathin
            self.folder, self.filename = os.path.split(pathin)
            self.find_relpath()
            #t2 = time.time()
            if get_os_data:
                self.get_os_data()
            #t3 = time.time()                
            if get_EXIF_data:
                self.read_EXIF_data()
                self.EXIF_date_to_attrs()
            #t4 = time.time()    
            if get_PIL_size:
                self.get_PIL_size()
            #t5 = time.time()
            if calc_md5:
                self.md5sum = md5sum.md5sum(self.pathin)
            #t6 = time.time()
            for attr in empty_attrs:
                setattr(self, attr, None)
            #t7 = time.time()
    ##         for i in range(2,7):
    ##             dt = 't%i-t%i' % (i, i-1)
    ##             exec('curt='+dt)
    ##             print(dt + '='+str(curt))

    def torow(self, photo_id):
        rowout = ['%i' % photo_id]
        for attr in cols:
            if attr != 'photo_id':
                val = getattr(self, attr)
                if val is None:
                    val = ''
                if rowout is None:
                    rowout = [val]
                else:
                    rowout.append(val)
        return rowout
        
class photo_db(spreadsheet.CSVSpreadSheet):
    def __init__(self, pathin, force_new=False, **kwargs):
        if os.path.isdir(pathin):
            self.folder = pathin
            pathin = self.find_latest_db()
            self.namein = None
        else:
            self.folder, self.namein = os.path.split(pathin)
            
        spreadsheet.CSVSpreadSheet.__init__(self, pathin, \
                                            colmap=colmap, \
                                            **kwargs)
        self.colmap = colmap
        self.next_id = 1
        if (not force_new) and os.path.exists(pathin):
            self.FindLabelRow('photo_id')
            self.FindDataColumns()
            self.MapCols()
            self.next_id = int(self.photo_id.astype(float).max()) + 1

        elif (not hasattr(self, 'labels')) or \
                 (self.labels == []) or \
                 (self.labels is None):
            #assume that if self.labels has been set, some sort of
            #initiation has already been done.
            self.labels = cols
            for attr in cols:
                setattr(self, attr, [])
        else:
            print('bypassing photo_db initialization')

        self.convert_cols_to_int()


    def search_for_row_by_photo_id(self, photo_id):
        if type(photo_id) != int:
            photo_id = int(float(photo_id))
        index_list = where(self.photo_id == photo_id)[0]
        assert len(index_list) == 1, 'Did not find exactly one match for ' + str(photo_id) + \
               ', index_list = ' + str(index_list)
        return index_list[0]


    def update_attr(self, photo_id, attr, value):
        assert attr != 'photo_id', 'You are not allowed to change the photo_id'
        row = self.search_for_row_by_photo_id(photo_id)
        vect = getattr(self, attr)
        vect[row] = value


    def copy_row_by_photo_id(self, photo_id):
        row = self.search_for_row_by_photo_id(photo_id)
        mycopy = copy.copy(self.alldata[row])
        return mycopy
        

    def good_data(self, item, label):
        out = True
        if label == 'rating':
            #print('rating = %s' % item)
            if item is None:
                out = False
            elif float(item) == 0.0:
                out = False
        elif label == 'tags':
            print('tag = %s' % item)
        return out


    def clean_zero_or_None(self, item):
        if item is None:
            item = ''
        elif float(item) == 0.0:
            item = ''
        return item
    

    def clean_data(self, item, label):
        if label in ['rating', 'tags']:
            item = self.clean_zero_or_None(item)
        return item
        
            

    def map_data_to_alldata(self, data, labels, colmap):
        revmap = dict((value,key) for key, value in colmap.iteritems())
        id_label = revmap['photo_id']
        assert id_label in labels, 'labels must include %s and the id must be a column of data.' % id_label
        id_ind = labels.index(id_label)
        id_col = self.labels.index('photo_id')
        colindmap = {}
        for label in labels:
            fulllabel = colmap[label]
            ind = self.labels.index(fulllabel)
            colindmap[label] = ind
            
            
        for row in data:
            photo_id = row[id_ind]
            alldata_row_ind = self.search_for_row_by_photo_id(photo_id)
            for item, label in zip(row, labels):
                col = colindmap[label]
                if col != id_col:
                    item = self.clean_data(item, label)
                    self.alldata[alldata_row_ind][col] = item
            
            
            
        


    def convert_cols_to_int(self):
        int_cols = ['photo_id','year','day','hour', 'minute', \
                    'PIL_width', 'PIL_height','rating']
        for col in int_cols:
            if hasattr(self, col):
                myvect = getattr(self, col)
                if type(myvect) == list:
                    myvect = array(myvect)
                myfloat = myvect.astype(float)
                myint = myfloat.astype(int)
                setattr(self, col, myint)


    def search_for_photo(self, photo):
        ind = None
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
        return ind
        
    def add_photo(self, photo, verbosity=1, copy=False):
        ind = self.search_for_photo(photo)
        if ind is not None:
            if verbosity > 0:
                print('photo already in dB:')
                print('  md5sum: ' + str(photo.md5sum))
                print('  filename: ' + photo.filename)
                print('  db filename: ' + self.filename[ind])
        else:
            for attr in cols:
                if attr != 'photo_id':#<-- the photos don't necessary know their own id'sg
                    val = getattr(photo, attr)
                    vect = getattr(self, attr)
                    if type(vect) == numpy.ndarray:
                        vect = numpy.append(vect, val)
                    else:
                        vect.append(val)
            self.alldata.append(photo.torow(self.next_id))
            self.next_id += 1
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
            #pathout = self.get_new_path()
            if self.namein is None:
                name = 'photo_db.csv'
            else:
                name = self.namein
            pathout = os.path.join(self.folder, name)
        self.WriteAllDataCSV(pathout, append=False)
        

if __name__ == '__main__':
    import file_finder
    #db_path = '/mnt/personal/pictures/Joshua_Ryan/photo_db.csv'
    #photo_db_12_21_09__19_35_11.csv'
    import socket

    hostname = socket.gethostname()

    if hostname == 'AM2':
        folder = '/home/ryan/git/personal/'
    else:
        folder = '/home/ryan/JoshuaRyan_on_AM2/'
        
    db_name = 'photo_db.csv'
    db_path = os.path.join(folder, db_name)
    force = 0
    mydb = photo_db(db_path, force_new=force)
#    folder = '/mnt/personal/pictures/Joshua_Ryan/2009/Dec_2009/Santa_Hat_Pictures/2009-12-17--12.48.31'
    #folder = '/mnt/personal/pictures/Joshua_Ryan/2009/Dec_2009/Santa_Hat_Pictures/'
    #folder = '/mnt/personal/pictures/Joshua_Ryan/2011/Mar_2011/Eli'
    #folder = '/mnt/personal/pictures/Joshua_Ryan/2011/Mar_2011/unsorted'
    #folder = '/mnt/personal/pictures/Joshua_Ryan/2011/Mar_2011/'
    #folder = '/mnt/personal/pictures/Joshua_Ryan/2011/'
    #folder = '/home/ryan/Pictures/'
    #image_finder = file_finder.Image_Finder(folder)
    #paths = image_finder.Find_All_Images()
    #paths = image_finder.Find_Images()
    #photos = [photo(path) for path in paths]
    #mydb.add_photos(photos)
    #mydb.save()

    path = '/mnt/personal/pictures/Joshua_Ryan/missy_exif_test.jpg'
    myphoto = photo(path)
    
    ## folder = '/home/ryan/Pictures/'
    ## image_finder = file_finder.Image_Finder(folder)
    ## paths = image_finder.Find_All_Images()
    ## #paths = image_finder.Find_Images()
    ## photos = [photo(path) for path in paths]
    ## mydb.add_photos(photos)
    ## mydb.save()

    #folder = '/mnt/personal/pictures/Joshua_Ryan/2007'
    #folder = '/mnt/personal/pictures/Joshua_Ryan/2007'
    
    #verifying that Silver HD photos are already in
    #folder = '/mnt/personal/from_SILVERHD/pictures/Joshua_Ryan/2007/ultrasound'

    root = '/mnt/personal/pictures/Joshua_Ryan/2008'

    import rwkos
    folder_names = rwkos.find_dirs(root)


    #for name in folder_names[2:3]:
    name = folder_names[6]#<-- stopped after index 6
    folder = os.path.join(root, name)
    image_finder = file_finder.Image_Finder(folder)
    paths = image_finder.Find_All_Images()
    photos = [photo(path) for path in paths]
    inds = [mydb.search_for_photo(photo) for photo in photos]


    bad_inds = []
    for i, photo in enumerate(photos):
        if not photo.exif_date:
            bad_inds.append(i)
            

    add_them = 1
    if add_them:
        default_year = 2008
        default_month = 'Jan'
        exif_dates = []
        for photo in photos:
            exif_dates.append(photo.exif_date)
            if not photo.exif_date:
                photo.year = default_year
                photo.month = default_month
                photo.day = 0
        

        mydb.add_photos(photos)
        mydb.save()
