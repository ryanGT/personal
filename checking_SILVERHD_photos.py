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

root = '/mnt/personal/from_SILVERHD/pictures/Joshua_Ryan/2009'
folder_names = rwkos.find_dirs(root)

for name in folder_names[0:1]:
    print('\n'*5)
    print('name = ' + name)
    folder = os.path.join(root, name)
    mychecker = photo_db.folder_checker(folder, mydb)
    mychecker.run()
