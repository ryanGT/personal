import sqlite3 as lite
import time, os, shutil, glob, re
from numpy import *

from IPython.core.debugger import Pdb

def get_all_rows_from_db(db_path):
    con = lite.connect(db_path)

    with con:
        con.row_factory = lite.Row
        cur = con.cursor()

        cur.execute("SELECT * from PhotoTable order by timestamp desc")

        rows = cur.fetchall()

    return rows


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

