import photo_db, os, rwkos, shutil, re

from file_finder import Image_Finder

def find_all_photos(pathin):
    myfinder = Image_Finder(pathin)
    pathsout = myfinder.Find_All_Images()
    return pathsout


def build_path(photo, root='/mnt/personal/pictures/Joshua_Ryan', \
               makedirs=True):
    """Build the fullpath to the folder where photo should be moved
    to, i.e. root/year/month_year/YYYY-MM-DD.  If makedirs is True,
    then then make all the folders in the tree as needed."""
    year_str = '%i' % photo.year
    year_folder = os.path.join(root, year_str)
    month_str = '%s_%s' % (photo.month, year_str)
    month_folder = os.path.join(year_folder, month_str)
    month_num = photo_db.inverse_month_map[photo.month]
    day_str = '%s-%0.2i-%0.2i' % (year_str, month_num, photo.day)
    day_path = os.path.join(month_folder, day_str)
    
    if makedirs:
        rwkos.make_dir(year_folder)
        rwkos.make_dir(month_folder)
        rwkos.make_dir(day_path)

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


def copy_one_image(pathin):
    myphoto = photo_db.photo(pathin, get_EXIF_data=True, \
                             get_os_data=True, calc_md5=False, \
                             get_PIL_size=False, basepath=None, dictin=None)
    destfolder = build_path(myphoto)
    src_folder, name = os.path.split(myphoto.pathin)
    new_name = renumber_filename(name)
    destpath = os.path.join(destfolder, new_name)
    shutil.move(myphoto.pathin, destpath)
    return myphoto, destpath



if __name__ == '__main__':
    mypath = '/home/ryan/Desktop/pics_2012/Apr_2012/unsorted'
    myimages = find_all_photos(mypath)
    for image in myimages:
        photo, dp = copy_one_image(image)
