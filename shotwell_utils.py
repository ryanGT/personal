import sqlite3 as lite
import time, os, shutil, glob, re, datetime
from numpy import *
import txt_mixin

from IPython.core.debugger import Pdb

def get_all_rows_from_db(db_path):
    con = lite.connect(db_path)

    with con:
        con.row_factory = lite.Row
        cur = con.cursor()

        cur.execute("SELECT * from PhotoTable order by timestamp desc")

        rows = cur.fetchall()

    return rows

def get_events(db_path):
    con = lite.connect(db_path)

    with con:
        con.row_factory = lite.Row
        cur = con.cursor()

        cur.execute("SELECT * from EventTable")

        rows = cur.fetchall()

    return rows


def get_video_rows_from_db(db_path):
    con = lite.connect(db_path)

    with con:
        con.row_factory = lite.Row
        cur = con.cursor()

        cur.execute("SELECT * from VideoTable order by timestamp desc")

        rows = cur.fetchall()

    return rows


def make_YMD_folders_if_necessary(day_path):
    if not os.path.exists(day_path):
        month_path, day = os.path.split(day_path)
        year_path, month = os.path.split(month_path)
        if not os.path.exists(year_path):
            os.mkdir(year_path)
        if not os.path.exists(month_path):
            os.mkdir(month_path)
        os.mkdir(day_path)
        

def move_one_row(row, root='/mnt/personal/pictures/shotwell'):
    fp = row['filename']
    src_folder, fn = os.path.split(fp)
    if fp.find(root) == 0:
        #do nothing
        return
    ymd_folder = row_to_YMD_folder(row)
    day_path = os.path.join(root, ymd_folder)
    make_YMD_folders_if_necessary(day_path)
    dst_path = os.path.join(day_path, fn)
    shutil.move(fp, dst_path)
    

def move_one_video_row(row, \
                       root='/mnt/personal/pictures/shotwell/moved_videos'):
    move_one_row(row, root=root)
                       
    
def rows_to_filenames(rowlist):
    filenames = [row['filename'] for row in rowlist]
    return filenames


def build_YMD(pathin):
    rest, day = os.path.split(pathin)
    rest, month = os.path.split(rest)
    rest, year = os.path.split(rest)
    rel = os.path.join(year, month, day)
    return rel


def build_YMDFN(pathin):
    rest, filename = os.path.split(pathin)
    date_rel = build_YMD(rest)
    rel = os.path.join(date_rel, filename)
    return rel


def filepaths_to_YMDFN_list(pathsin):
    paths_out = []

    for curpath in pathsin:
        rel = build_YMDFN(curpath)
        paths_out.append(rel)

    return paths_out


def paths_to_fno(pathsin):
    filenames_out = []
    
    for curpath in pathsin:
        folder, fno = os.path.split(curpath)
        filenames_out.append(fno)

    return filenames_out


def find_folders(paths):
    folders = []
    for curpath in paths:
        folder, filename = os.path.split(curpath)
        folders.append(folder)

    return folders


def is_jpg(pathin):
    pne, ext = os.path.splitext(pathin)
    return ext.lower() == '.jpg'


def is_not_jpg(pathin):
    return not is_jpg(pathin)


std_pat = re.compile('(DSC|D7K|100)_([0-9]{4})\\.(JPG|jpg)')


def is_standard_filename(pathin):
    pne, filename = os.path.split(pathin)
    return bool(std_pat.match(filename))


def get_jpg_num(pathin):
    pne, filename = os.path.split(pathin)    
    q = std_pat.match(filename)
    return int(q.group(2))


def find_other_files(folder):
    allfiles = glob.glob(os.path.join(folder, '*'))
    other_paths = filter(is_not_jpg, allfiles)
    other_files = []
    for curpath in other_paths:
        folder, filename = os.path.split(curpath)
        other_files.append(filename)
    other_files.sort()
    return other_files


def print_row(rowin):
    keys = rowin.keys()

    for key in keys:
        val = rowin[key]
        print('%s: %s' % (key,val))


def row_to_YMD_folder(row):
    seconds = row['timestamp']
    dt_obj = datetime.datetime.fromtimestamp(seconds)
    folder = os.path.join(str(dt_obj.year), str(dt_obj.month), str(dt_obj.day))
    return folder


def row_to_relpath(row):
    fp = row['filename']
    folder, fn = os.path.split(fp)
    ymd_folder = row_to_YMD_folder(row)
    return os.path.join(ymd_folder, fn)


class shotwell_db(object):
    def _path_stuff(self):
        self.allpaths = rows_to_filenames(self.allrows)
        self.relpaths = filepaths_to_YMDFN_list(self.allpaths)
        self.filenames = txt_mixin.txt_list(paths_to_fno(self.allpaths))

        
    def __init__(self, db_path):
        self.allrows = get_all_rows_from_db(db_path)
        self._path_stuff()


    def find_not_copied_in(self):
        not_copied_inds = []
        for ind, curpath in enumerate(self.allpaths):
            if curpath.find('/mnt/personal/pictures/shotwell') != 0:
                not_copied_inds.append(ind)
        return not_copied_inds


    def inds_to_paths(self, inds):
        path_array = array(self.allpaths)
        paths_out = path_array[inds]
        return paths_out


    def find_matching_folder(self, folder):
        not_copied_inds = []
        
        for ind, curpath in enumerate(self.allpaths):
            if curpath.find(folder) == 0:
                not_copied_inds.append(ind)
                
        return not_copied_inds


    def find_relpath_from_timestamp(self, ind):
        row = self.allrows[ind]
        relpath = row_to_relpath(row)
        return relpath
       
        

    def search_using_fno(self, filepath):
        folder, fno = os.path.split(filepath)
        inds = self.filenames.findall(fno)
        if inds:
            list_out = []
            for ind in inds:
                list_out.append(self.allpaths[ind])
            return list_out



    def move_a_list_of_inds(self, inds):
        for ind in inds:
            move_one_row(self.allrows[ind])
        

class shotwell_video_db(shotwell_db):
    def __init__(self, db_path):
        self.allrows = get_video_rows_from_db(db_path)
        self._path_stuff()





if __name__ == '__main__':
    folder = '/mnt/personal/pictures/krauss_photos/2012'
    db_path ='/mnt/personal/pictures/shotwell/db/data/photo.db'
    photo_db = shotwell_db(db_path)
    video_db = shotwell_video_db(db_path)
    photo_inds = photo_db.find_matching_folder(folder)
    video_inds = video_db.find_matching_folder(folder)
    
    
