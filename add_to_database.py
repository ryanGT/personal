import photo_db
import file_finder
import socket, os

from numpy import loadtxt

hostname = socket.gethostname()

if hostname == 'AM2':
    folder = '/home/ryan/git/personal/'
else:
    folder = '/home/ryan/JoshuaRyan_on_AM2/'

db_name = 'photo_db.csv'
db_path = os.path.join(folder, db_name)
force = 0
mydb = photo_db.photo_db(db_path, force_new=force)

import rwkos, txt_mixin

from optparse import OptionParser

usage = 'usage: %prog [options]'
parser = OptionParser(usage)


## parser.add_option("-i", "--ind", dest="ind", \
##                   help="folder index to add to the db", \
##                   default=-1, type=int)

## parser.add_option("-m", "--month", dest="month", \
##                      help="default month for bad EXIF date cases", \
##                      default="", type=str)

## parser.add_option("-y", "--year", dest="year", \
##                      help="default year for bad EXIF date cases", \
##                      default=2008, type=int)

parser.add_option("-a", action="store_true", dest="add_them", \
                  help="add photos to the db")
parser.set_defaults(add_them=False)

(options, args) = parser.parse_args()

## ind = options.ind
## default_month = options.month
default_year = 2009
add_them = options.add_them

month_data = loadtxt('2009_months.csv',delimiter=',',dtype=str)
month_dict = dict(zip(month_data[:,0],month_data[:,1]))

root = '/mnt/personal/pictures/Joshua_Ryan/2009'
folder_names = rwkos.find_dirs(root)

#txt_mixin.dump('2009_months.csv', folder_names)

## # New adding code

for name in folder_names[3:4]:
    folder = os.path.join(root, name)

    default_month = month_dict[name]

    mychecker = photo_db.folder_checker_and_adder(folder, mydb, \
                                                  default_year=default_year, \
                                                  default_month=default_month)
    mychecker.check()


    if add_them:
        if mychecker.num_not_in > 0:
            total = float(mychecker.num_not_in + mychecker.num_in)
            p = float(mychecker.num_not_in)/total
            if p > 0.9:
                mychecker.add_photos_to_db() 

