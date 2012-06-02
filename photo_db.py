from scipy import *
import numpy
import spreadsheet, EXIF, csv, txt_mixin
import os, time, md5sum, re, glob, pdb
from PIL import Image
#import odict
import file_finder

from IPython.core.debugger import Pdb

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
            'EXIF DateTimeDigitized':'exif_date_digitized', \
            'Image Model':'exif_camera', \
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
        'md5sum','exif_camera']

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

inverse_month_map = dict((val,key) for key, val in month_map.iteritems())

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

#class photo_db(spreadsheet.CSVSpreadSheet):
class photo_db(object):
    def _col_labels_to_attr_names(self):
        """Replace any spaces or other illegal characters in the
        column labels to make them into legal attr names."""
        illegal_chars = [' ',':','/','\\']
        attr_names = []
        for label in self.labels:
            attr = label
            for char in illegal_chars:
                attr = attr.replace(char, '_')
            attr_names.append(attr)
        self.attr_names = attr_names
        

    def map_cols_to_attr(self):
        """make each column of self.data an attribute of the db
        instance."""
        for attr, label in zip(self.attr_names, self.labels):
            col_ind = self.col_inds[label]
            setattr(self, attr, self.data[:,col_ind])
                    
        
    def __init__(self, pathin, force_new=False, **kwargs):
        if os.path.isdir(pathin):
            self.folder = pathin
            pathin = self.find_latest_db()
            self.namein = None
        else:
            self.folder, self.namein = os.path.split(pathin)

        data = loadtxt(pathin,dtype=str,delimiter=',')
        self.labels = data[0,:]
        self.data = data[1:,:]
        self.N_cols = len(self.labels)
        inds = range(self.N_cols)
        self.col_inds = dict(zip(self.labels, inds))
        self._col_labels_to_attr_names()
        self.map_cols_to_attr()
        self.convert_cols_to_int()
        
        ## spreadsheet.CSVSpreadSheet.__init__(self, pathin, \
        ##                                     colmap=colmap, \
        ##                                     **kwargs)
        ## self.colmap = colmap
        ## self.next_id = 1
        ## if (not force_new) and os.path.exists(pathin):
        ##     self.FindLabelRow('photo_id')
        ##     self.FindDataColumns()
        ##     self.MapCols()
        ##     self.next_id = int(self.photo_id.astype(float).max()) + 1

        ## elif (not hasattr(self, 'labels')) or \
        ##          (self.labels == []) or \
        ##          (self.labels is None):
        ##     #assume that if self.labels has been set, some sort of
        ##     #initiation has already been done.
        ##     self.labels = cols
        ##     for attr in cols:
        ##         setattr(self, attr, [])
        ## else:
        ##     print('bypassing photo_db initialization')
        ## self.convert_cols_to_int()


    def search_for_row_by_photo_id(self, photo_id):
        if type(photo_id) != int:
            photo_id = int(float(photo_id))
        index_list = where(self.photo_id == photo_id)[0]
        assert len(index_list) == 1, 'Did not find exactly one match for ' + str(photo_id) + \
               ', index_list = ' + str(index_list)
        return index_list[0]


    def update_alldata(self, photo_id, attr, value):
        #in order for this to work correctly, you need to find the correct
        #row and column of self.alldata where value should be stored.
        alldata_row_ind = self.search_for_row_by_photo_id(photo_id)
        col_ind = self.labels.index(attr)
        self.alldata[alldata_row_ind][col_ind] = value


    def update_attr(self, photo_id, attr, value, update_alldata=True):
        #note that this method does not change self.alldata, so things
        #don't actually get saved
        assert attr != 'photo_id', 'You are not allowed to change the photo_id'
        row = self.search_for_row_by_photo_id(photo_id)
        vect = getattr(self, attr)
        vect[row] = value
        if update_alldata:
            self.update_alldata(photo_id, attr, value)


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

    def _empty_strings_to_0(self, vect):
        """Replace all empty strings with '0' so that they can be
        converted to floats."""
        inds = where(vect=='')[0]
        vect[inds] = '0'
        return vect

    def convert_cols_to_int(self):
        int_cols = ['photo_id','year','day','hour', 'minute', \
                    'PIL_width', 'PIL_height','rating']
        for col in int_cols:
            if hasattr(self, col):
                myvect = getattr(self, col)
                if type(myvect) == list:
                    myvect = array(myvect)
                myvect = self._empty_strings_to_0(myvect)
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



class folder_checker(object):
    """This class takes a top level folder path as an input and checks
    to see which of the photos in that folder (and all of its
    subfolders) are in the database."""
    def __init__(self, topfolder, database):
        self.topfolder = topfolder
        self.database = database
        self.image_finder = file_finder.Image_Finder(self.topfolder)


    def find_all_images(self):
        self.image_paths = self.image_finder.Find_All_Images()


    def create_photo_list(self):
        self.photos = [photo(path) for path in self.image_paths]


    def search_db_for_photos(self):
        N = len(self.image_paths)
        self.boolvect = numpy.zeros(N)
        self.inds = []
        self.photos_in = []
        self.photos_not_in = []
        for i, photo in enumerate(self.photos):
            ind = self.database.search_for_photo(photo)
            self.inds.append(ind)
            if ind is None:
                self.boolvect[i] = 0#redundant, this should already be 0
                self.photos_not_in.append(photo)
            else:
                self.boolvect[i] = 1
                self.photos_in.append(photo)

        self.num_in = len(self.photos_in)
        self.num_not_in = len(self.photos_not_in)


    def print_results(self):
        print('')
        print('='*20)
        print('topfolder = ' + self.topfolder)
        print('# already in = ' + str(self.num_in))
        print('# not in = ' + str(self.num_not_in))


    def print_not_in(self):
        for i, photo in enumerate(self.photos_not_in):
            print('%i: %s' % (i,photo.pathin))



    def _build_html_header(self, title='Photos not in the database'):
        self.html_header = ['<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">']
        out = self.html_header.append
        out('<html>')
        out('<head>')
        out('<style type="text/css">')
        out('img {')
        out('    border:2px;')
        out('    margin:10px;')
        out('     margin-bottom:2px;')
        out('    }')
        out('')
        out('img.h90{')
        out('    height:90%;')
        out('    } ')
        out('img.w95{')
        out('    width:95%;')
        out('    } ')
        out('</style>')
        out('<title>%s</title>' % title)
        out('</head>')
        out('<body>')
        out('<h1>%s</h1>' % title)
        out('<TABLE>')


    def html_one_photo(self, photo_in, subfolder='900by600'):
        folder, name = os.path.split(photo_in.pathin)
        screensize_folder = os.path.join(folder, subfolder)
        fullpath = os.path.join(screensize_folder, name)
        out = self.html.append
        out('<TR align=center>')
        out('        <TD>')
        out('<img src="%s">' % fullpath)
        out('        </TD>')
        out('</TR>')
        out('')


    def html_report_not_in(self, filename):
        self._build_html_header()
        self.html = self.html_header

        for photo_i in self.photos_not_in:
            self.html_one_photo(photo_i)

        self.html.append('</TABLE>')
        self.html.append('</html>')
        txt_mixin.dump(filename, self.html)


    def run(self, verbosity=1):
        self.find_all_images()
        self.create_photo_list()
        self.search_db_for_photos()
        if verbosity > 0:
            self.print_results()


class folder_checker_and_adder(folder_checker):
    """This class takes a top level folder path as an input and checks
    to see which of the photos in that folder (and all of its
    subfolders) are in the database.  You can then add the photos not
    in the database to the database."""
    def __init__(self, topfolder, database, default_year, default_month):
        folder_checker.__init__(self, topfolder, database)
        self.default_year = default_year
        self.default_month = default_month



    def add_photos_to_db(self):
        exif_dates = []
        for photo_i in self.photos_not_in:
            exif_dates.append(photo_i.exif_date)
            if not photo_i.exif_date:
                photo_i.year = self.default_year
                photo_i.month = self.default_month
                photo_i.day = 0

        self.exif_dates = exif_dates
        self.database.add_photos(self.photos_not_in)
        self.database.save()

    def check(self):
        folder_checker.run(self)


if __name__ == '__main__':
    ###########################################
    #
    # Photo DB to do list:
    #
    # - rename and add 0's to the early D7000 pictures
    # - renumber D60 pictures with odometer based on dates
    # - create GUI for adding folders to the DB
    # - crate a means for generating an HTML report of
    #   pictures not in vs. in the database
    # - add all remaining Joshua_Ryan pictures to the database
    #
    #   - create a way to verify that an entire toplevel folder is in the DB
    #     (i.e. all of 2008)
    #
    # - add pictures not in Joshua_Ryan to the DB (copying or
    #   moving as necessary)
    #
    ###########################################
    import file_finder
    #db_path = '/mnt/personal/pictures/Joshua_Ryan/photo_db.csv'
    #photo_db_12_21_09__19_35_11.csv'
    import socket

    hostname = socket.gethostname()

    if hostname == 'AM2':
        folder = '/home/ryan/git/personal/'
    else:
        remote = 0
        if remote:
            folder = '/home/ryan/JoshuaRyan_on_AM2/'
        else:
            folder = '/home/ryan/git/personal/'

    db_name = 'photo_db.csv'
    db_path = os.path.join(folder, db_name)
    force = 0
    t1 = time.time()
    mydb = photo_db(db_path, force_new=force)
    t2 = time.time()
    print('time to create photo_db = ' + str(t2-t1))
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

    ## path = '/mnt/personal/pictures/Joshua_Ryan/missy_exif_test.jpg'
    ## myphoto = photo(path)

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

    #root = '/mnt/personal/pictures/Joshua_Ryan/2008'

    import rwkos

    from optparse import OptionParser

    usage = 'usage: %prog [options]'
    parser = OptionParser(usage)


    parser.add_option("-i", "--ind", dest="ind", \
                      help="folder index to add to the db", \
                      default=-1, type=int)

    parser.add_option("-m", "--month", dest="month", \
                         help="default month for bad EXIF date cases", \
                         default="", type=str)

    parser.add_option("-y", "--year", dest="year", \
                         help="default year for bad EXIF date cases", \
                         default=2008, type=int)

    parser.add_option("-a", action="store_true", dest="add_them", \
                      help="add photos to the db")
    parser.set_defaults(add_them=False)

    (options, args) = parser.parse_args()

    ind = options.ind
    default_month = options.month
    default_year = options.year
    add_them = options.add_them

    month_data = loadtxt('2008_months.csv',delimiter=',',dtype=str)
    month_dict = dict(zip(month_data[:,0],month_data[:,1]))


    ## # New adding code
    ## root = '/mnt/personal/pictures/Joshua_Ryan/2008'
    ## folder_names = rwkos.find_dirs(root)
    ## name = folder_names[ind]
    ## folder = os.path.join(root, name)

    ## if not default_month:
    ##     default_month = month_dict[name]

    ## mychecker = folder_checker_and_adder(folder, mydb, \
    ##                                      default_year=default_year, \
    ##                                      default_month=default_month)
    ## mychecker.check()


    ## if add_them:
    ##     if mychecker.num_not_in > 0:
    ##         total = mychecker.num_not_in + mychecker.num_in
    ##         p = mychecker.num_not_in/total
    ##         if p > 0.9:
    ##             mychecker.add_photos_to_db()

    ## #Adding code
    ## #for name in folder_names[2:3]:
    ## name = folder_names[ind]#<-- stopped after index 6
    ## folder = os.path.join(root, name)
    ## image_finder = file_finder.Image_Finder(folder)
    ## paths = image_finder.Find_All_Images()
    ## photos = [photo(path) for path in paths]
    ## inds = [mydb.search_for_photo(photo_i) for photo_i in photos]


    ## bad_inds = []
    ## for i, photo_i in enumerate(photos):
    ##     if not photo_i.exif_date:
    ##         bad_inds.append(i)


    ## if add_them:
    ##     exif_dates = []
    ##     for photo_i in photos:
    ##         exif_dates.append(photo_i.exif_date)
    ##         if not photo_i.exif_date:
    ##             photo_i.year = default_year
    ##             photo_i.month = default_month
    ##             photo_i.day = 0


    ##     mydb.add_photos(photos)
    ##     mydb.save()


    ## # Checking code
    ## # Verifying which SILVERHD folders are already in the DB
    ## root = '/mnt/personal/from_SILVERHD/pictures/Joshua_Ryan/2008'
    ## folder_names = rwkos.find_dirs(root)
    ## name = folder_names[ind]
    ## folder = os.path.join(root, name)
    ## mychecker = folder_checker(folder, mydb)
    ## mychecker.run()


    ## Adding the exif_camera column
    # I think this is done
    ## root = '/mnt/personal/pictures/Joshua_Ryan/'

    ## for ind in range(5000,5642):
    ##     rp = mydb.relpath[ind]
    ##     photofolder = os.path.join(root, rp)
    ##     fn = mydb.filename[ind]
    ##     photopath = os.path.join(photofolder, fn)
    ##     cur_photo = photo(photopath)
    ##     photo_id = mydb.photo_id[ind]
    ##     mydb.update_attr(photo_id, 'exif_camera', cur_photo.exif_camera)


    ## mydb.save()
