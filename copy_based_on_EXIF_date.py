import photo_db, os, rwkos, shutil, re, glob, file_finder
import time
import pdb

from file_finder import Image_Finder

def find_all_photos(pathin):
    myfinder = Image_Finder(pathin)
    pathsout = myfinder.Find_All_Images()
    return pathsout


def _build_path(year_str, month_str, day_str, \
                root=None, makedirs=True):
    if root is None:
        root = '/mnt/personal/pictures/Joshua_Ryan/'
        
    year_folder = os.path.join(root, year_str)
    month_folder_name = os.path.join(year_folder, month_str)
    day_path = os.path.join(month_folder_name, day_str)
    
    if makedirs:
        rwkos.make_dir(year_folder)
        rwkos.make_dir(month_folder_name)
        rwkos.make_dir(day_path)

    return day_path


def month_folder(month_int_str, year_str):
    month_abbrev = photo_db.month_map[int(month_int_str)]
    month_folder_name = '%s_%s' % (month_abbrev, year_str)
    return month_folder_name


def day_folder(day_str, month_int_str, year_str):
    month_int = int(month_int_str)
    day_int = int(day_str)
    day_folder_name = '%s-%0.2i-%0.2i' % (year_str, month_int, day_int)
    return day_folder_name


def build_path(photo, root=None, makedirs=True):
    """Build the fullpath to the folder where photo should be moved
    to, i.e. root/year/month_year/YYYY-MM-DD.  If makedirs is True,
    then then make all the folders in the tree as needed."""
    year_str = '%i' % photo.year
    month_str = '%s_%s' % (photo.month, year_str)
    month_num = photo_db.inverse_month_map[photo.month]
    day_str = '%s-%0.2i-%0.2i' % (year_str, month_num, photo.day)
    
    day_path = _build_path(year_str, month_str, day_str, \
                           root=root, \
                           makedirs=makedirs)
    return day_path


p = re.compile('(.*)_([0-9]+)')

def renumber_filename(namein, add_to=0, fmt='%0.6i'):
    """In order to prevent many files with the same 4 digit number
    from floating around on my computer, switch the numbers to 6
    digits and add the base add_to to the number (eventually add_to
    with take on values like 10000 as the odometer on the camera
    flips)."""
    fno, ext = os.path.splitext(namein)
    q = p.match(fno)
    num_str = q.group(2)
    num_int = int(num_str)
    new_num = num_int + add_to
    new_num_str = fmt % new_num
    new_fno = '%s_%s' % (q.group(1), new_num_str)
    new_filename = new_fno + ext
    return new_filename


last_four_digits_pat = re.compile('(.*)([0-9]{4})')#insist on 4 digits at the end

def separate_filename(pathin):
    folder, filename = os.path.split(pathin)
    fno, ext = os.path.splitext(filename)

    q = last_four_digits_pat.search(fno)
    return q.group(1), int(q.group(2))


def find_file_number(pathin):
    pre_str, mynum = separate_filename(pathin)
    return mynum


def find_max_and_min_file_numbers(folderpath):
    """Assuming path contains picture and movie files that end in
    digits, find the highest and lowest digit based on sorting the
    paths."""
    myfinder = file_finder.Multi_Media_Finder(curdir)
    files = myfinder.Find_Top_Level_Files()
    files.sort()
    first_file = files[0]
    last_file = files[-1]

    low_num = find_file_number(first_file)
    high_num = find_file_number(last_file)
    return high_num, low_num
    
def copy_one_image(pathin, root=None):
    myphoto = photo_db.photo(pathin, get_EXIF_data=True, \
                             get_os_data=True, calc_md5=False, \
                             get_PIL_size=False, basepath=None, dictin=None)
    destfolder = build_path(myphoto, root=root)
    src_folder, name = os.path.split(myphoto.pathin)
    new_name = renumber_filename(name)
    destpath = os.path.join(destfolder, new_name)
    shutil.move(myphoto.pathin, destpath)
    return myphoto, destpath


def _find_photo(pathin, inc=-1):
    folder, filename = os.path.split(pathin)
    part1, num_in = separate_filename(pathin)
    
    found = False

    myfinder = file_finder.Multi_Media_Finder(folder)
    files = myfinder.Find_Top_Level_Files()
    files.sort()
    N = len(files)
    
    index_in = files.index(pathin)

    test_index = index_in + inc

    exif_exts = ['.jpg','.nef','.cr2']
    
    while -1 < test_index < N:
        test_path = files[test_index]
        pne, ext = os.path.splitext(test_path)
        if ext.lower() in exif_exts:
            return test_path
        else:
            test_index += inc
    
    ## max_num, min_num = find_max_and_min_file_numbers(folder)
    
    ## while abs(i) < 1000:
    ##     test_num = num_in + inc
    ##     pat = part1 + str(test_num) + '.*'
    ##     full_pat = os.path.join(folder, pat)
    ##     matches = glob.glob(full_pat)
    ##     if not matches:
    ##         #glob returned an empty list; if a file was deleted this
    ##         #might not mean anything.  How do we find the lowest
    ##         #numbered file in a diretory?
    ##         if (test_num < min_num) or (test_num > max_num):
    ##             #we didn't find the next photo
    ##             break

def split_EXIF_date(date_str):
    date, time = date_str.split(' ',1)
    return date.strip()


def get_EXIF_date(pathin):
    myphoto = photo_db.photo(pathin, get_EXIF_data=True, \
                             get_os_data=True, calc_md5=False, \
                             get_PIL_size=False, basepath=None, dictin=None)    
    return myphoto.exif_date


def find_previous_photo(pathin):
    return _find_photo(pathin, inc=-1)


def find_next_photo(pathin):
    return _find_photo(pathin, inc=1)

fmt = '%Y:%m:%d'

def getctime_str(pathin):
    sec1 = os.path.getctime(pathin)
    struct1 = time.localtime(sec1)
    str1 = time.strftime(fmt, struct1)
    return str1


def datestr_to_time(datestr):
    t1 = time.strptime(datestr,fmt)
    return t1


def get_movie_date(pathin):
    """determine the date associated with a movie file based on a
    combination of the EXIF date of the next and previous still image
    in the directory and the os.path.getctime of the movie file."""
    #pdb.set_trace()
    prev_photo = find_previous_photo(pathin)
    next_photo = find_next_photo(pathin)
    print('pathin = ' + pathin)
    print('prev_photo = ' + str(prev_photo))
    print('next_photo = ' + str(next_photo))

    if next_photo is None:
        next_date = None
    else:
        next_date = split_EXIF_date(get_EXIF_date(next_photo))

    if prev_photo is None:
        prev_date = None
    else:
        prev_date = split_EXIF_date(get_EXIF_date(prev_photo))
    
    ctime_str = getctime_str(pathin)

    ## print('prev_date = ' + prev_date)
    ## print('next_date = ' + next_date)
    ## print('ctime_str = ' + ctime_str)

    if prev_date == next_date:
        return prev_date
    elif (ctime_str == prev_date) or (ctime_str == next_date):
        return ctime_str
    else:
        t_prev = datestr_to_time(prev_date)
        t_next = datestr_to_time(next_date)
        t_ctime = datestr_to_time(ctime_str)
        if t_next > t_ctime > t_prev:
            return ctime_str
        else:
            return None


def copy_one_movie_file(pathin, root=None):
    """It is tricky to find the date for an movie file, because they
    don't seem to work with EXIF.  My plan is to find the EXIF date of
    the next and previous numbered still image file and compare them
    to the os.getctime date.  If 2 of the 3 agree, use that date."""
    date_str = get_movie_date(pathin)
    assert date_str is not None, "did not find a valid date for " + pathin
    year_str, month_str, day_str = date_str.split(':',2)
    day_folder_name = day_folder(day_str, month_str, year_str)
    month_folder_name = month_folder(month_str, year_str)
    destfolder =_build_path(year_str, month_folder_name, day_folder_name, \
                            root=root, makedirs=True)
    src_folder, name = os.path.split(pathin)
    new_name = renumber_filename(name)
    destpath = os.path.join(destfolder, new_name)
    ## print('--------------------')
    ## print('pathin = ' + pathin)
    ## print('destpath = ' + destpath)
    shutil.move(pathin, destpath)
    return destpath


def find_gvfs_path(verbosity=1):
    homedir = os.path.expanduser('~')
    gvfs_path = os.path.join(homedir, '.gvfs')
    if not os.path.exists(gvfs_path):
        if verbosity > 0:
            print('did not find ' + gvfs_path)
        return None
    dirs1 = os.listdir(gvfs_path)
    assert len(dirs1) == 1, "did not find exactly one folder in gvfs_path: %s" % \
           dirs1
    usb_folder = dirs1[0]
    assert usb_folder.find('mount on usb') > -1, "did not find mount on usb in usb_folder: " + usb_folder
    usb_path = os.path.join(gvfs_path, usb_folder)
    dirs2 = os.listdir(usb_path)
    assert len(dirs2) in [1,2], "did not find one or two folders in usb_path. dirs2 = " + str(dirs2)
    if len(dirs2) == 2:
        myfolder = dirs2[0]
        assert myfolder.find('store_0001') == 0, "myfolder did not start with store_0001: " + myfolder
    else:
        myfolder = dirs2[0]

    myroot = os.path.join(usb_path, myfolder)
    
    return myroot
    
    
if __name__ == '__main__':
    ## mypath = '/home/ryan/Desktop/pics_2012/Apr_2012/unsorted'
    ## myimages = find_all_photos(mypath)
    ## for image in myimages:
    ##     photo, dp = copy_one_image(image)

    
    mypath = '/media/NIKON D7000/DCIM/100D7000'
    mov_pat = os.path.join(mypath, '*.MOV')
    mov_files = glob.glob(mov_pat)
    #for mov_file in mov_files[0:1]:
    for mov_file in mov_files:
        mydate = copy_one_movie_file(mov_file)
    
