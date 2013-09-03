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
