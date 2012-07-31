#!/usr/bin/env python
import pygtk
pygtk.require('2.0')
import gtk
import glob, os, pdb, socket, shutil, datetime, time, numpy

import rwkmisc, listbox, thumbnail_viewer, image_on_scrolled_window


settings_path = 'settings_photo_app.pkl'

import rwkos, photo_db
myname = socket.gethostname()

month_list = [photo_db.month_map[ind] for ind in range(1,13)]

import copy

if myname == 'AM2':
    if rwkos.amiLinux():
        myroot = '/mnt/personal/pictures/Joshua_Ryan'
elif myname == 'hpdv4':
    myroot = '/home/ryan/JoshuaRyan_on_AM2'
    if not os.path.exists(myroot):
        print('You have not mounted the AM2 pictures folder.')
        print('please run the script ~/scripts/mount_Joshua_pics')
        myroot = None


# Database columns:
#
# - filename
# - relpath<-- use rel rather than full
# - folder
# - year
# - month
# - md5sum
# - EXIF date?
# - ctime?
# - mtime?
# - rating
# - tags

ss_folder_name = '900by600'#name of folder containing screensize images

def thumbpath_to_screensize(thumb_path):
    thumb_folder, fn = os.path.split(thumb_path)
    folder, thumb_dir = os.path.split(thumb_folder)
    ss_folder = os.path.join(folder, ss_folder_name)
    ss_path = os.path.join(ss_folder, fn)
    return ss_path

    
def csv_open_dialog():
    dialog = gtk.FileChooserDialog("Open..",
                                   None,
                                   gtk.FILE_CHOOSER_ACTION_SAVE,
                                   #gtk.FILE_CHOOSER_ACTION_OPEN,
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_OPEN, gtk.RESPONSE_OK))
                                   #gtk.STOCK_SAVE, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)
    dialog.set_current_name('photo_db.csv')
    dialog.set_current_folder(myroot)
    
    filter = gtk.FileFilter()
    filter.set_name("CSV files")
    filter.add_pattern("*.csv")
    dialog.add_filter(filter)

    filter = gtk.FileFilter()
    filter.set_name("All files")
    filter.add_pattern("*")
    dialog.add_filter(filter)


    response = dialog.run()
    if response == gtk.RESPONSE_OK:
        print dialog.get_filename(), 'selected'
        out = dialog.get_filename()
    elif response == gtk.RESPONSE_CANCEL:
        print 'Closed, no files selected'
        out = None
    dialog.destroy()

    return out



class listview_on_scrolledwindow(gtk.ScrolledWindow):
    def set_data(self, data=None, clear=True):
        if data is None:
            data = self.data
        if clear:
            self.model.clear()
        for row in data:
            self.model.append(row)


    def _init_view(self):
        self.modelfilter = self.model.filter_new()
        self.model.clear()
        # create the TreeView
        self.treeview = gtk.TreeView()


        N = len(self.labels)
        # create the TreeViewColumns to display the data
        self.treeview.columns = [None]*N
        for i, label in enumerate(self.labels):
            self.treeview.columns[i] = gtk.TreeViewColumn(label)

        #self.modelfilter.set_visible_func(self.visible_cb, self.show_states)
        #self.treeview.set_model(self.modelfilter)
        self.treeview.set_model(self.model)

        for n in range(N):
            # add columns to treeview
            self.treeview.append_column(self.treeview.columns[n])
            # create a CellRenderers to render the data
            self.treeview.columns[n].cell = gtk.CellRendererText()
            # add the cells to the columns
            self.treeview.columns[n].pack_start(self.treeview.columns[n].cell,
                                                True)
            # set the cell attributes to the appropriate liststore column
            self.treeview.columns[n].set_attributes(
                self.treeview.columns[n].cell, text=n)


        # make treeview searchable
        self.treeview.set_search_column(0)
        


    def match_func(self, iter, data):
        column, key = data # data is a tuple containing column number, key
        value = self.model.get_value(iter, column)
        return value == key

    
    def search(self, iter, data):
        while iter:
            if self.match_func(iter, data):
                return iter
            result = self.search(self.model.iter_children(iter),  data)
            if result: return result
            iter = self.model.iter_next(iter)
        return None



    def find_row_by_photo_id(self, photo_id):
        match_iter = self.search(self.model.iter_children(None), \
                                 (0, photo_id))
        return match_iter

        
    def __init__(self, data, dtype_list, labels, modelclass=gtk.ListStore):
        gtk.ScrolledWindow.__init__(self)
        #print('data = ' + str(data))
        self.data = data
        self.dtype_list = dtype_list
        self.labels = labels
        self.model = modelclass(*self.dtype_list)
        self.set_data()
        self._init_view()
        gtk.Container.add(self, self.treeview)
        self.show()

        
        

class photo_app(rwkmisc.object_that_saves):

    # This is a callback function. The data arguments are ignored
    # in this example. More on callbacks below.
    def hello(self, widget, data=None):
        print "Hello World"


    def next_image_method(self, widget, data=None):
        print "in next_image_method"
        self.thumbs_viewer.select_next()


    def prev_image_method(self, widget, data=None):
        print "in prev_image_method"
        self.thumbs_viewer.select_previous()


    def on_delete_button(self, widget, data=None):
        print "in on_delete_button"
        pdb.set_trace()
        photo_ids = self.get_selected_photo_ids()
        for photo_id in photo_ids:
            self.delete_one_photo(photo_id)
            



    def add_directory(self, widget, data=None):
        print "in add_directory"


    def search_for_list_in_attr(self, attr, searchlist):
        """Search for each element of list in the attr of self.db.
        Return the elements of searchlist that are present in the
        column."""
        outlist = []

        for elem in searchlist:
            boolvect = self.db.SearchAttr(elem, attr)
            if boolvect.any():
                outlist.append(elem)
        return outlist


    def _find_all(self, attr, filter=False):
        vect = getattr(self.db, attr)
        if filter and hasattr(self, 'boolvect'):
            vect = vect[self.boolvect]
        out = numpy.unique(vect)
        return out
    
        
    def find_all_years(self, **kwargs):
        ## #out = datetime.date.today()
        ## #curyear = out.year
        ## #search_years = range(2000, curyear+1)
        ## #found_years = self.search_for_list_in_attr('year', search_years)
        ## found_years = numpy.unique(self.db.year)
        ## print('found_years = ' + str(found_years))
        ## return found_years
        return self._find_all(attr='year', **kwargs)
    


    def find_all_months(self, **kwargs):
        ## #found_months = self.search_for_list_in_attr('month', month_list)
        ## found_months = numpy.unique(self.db.month)
        ## print('found_months = ' + str(found_months))
        ## return found_months
        return self._find_all(attr='month', **kwargs)
    

    def find_all_folders(self, **kwargs):
        ## unique_folders = numpy.unique(self.db.folder_name)
        ## print('unique_folders = ' + str(unique_folders))
        ## return unique_folders
        return self._find_all(attr='folder_name', **kwargs)

        
    def load_db(self):
        #print "in load_db"
        assert os.path.exists(self.database_path), \
               'Could not find db file %s' % self.database_path
        force = 0
        self.db = photo_db.photo_db(self.database_path, \
                                    force_new=force)
        nr, nc = self.db.data.shape
        self.num_found_entry.set_text('%i' % nr)


    def _get_data(self):
        #I need to add ratings and tags to the displayed data.  I also
        #need to include the photo id # in undisplayed data.  Then I
        #need to be able to use the id # as an index when changes are
        #made to ratings or tags.  Finally I need to use the id # to
        #map changes back into self.db.whereever so that I can save
        #the changes.
        if hasattr(self, 'db'):
            data = numpy.column_stack([self.db.photo_id, \
                                       self.db.filename, self.db.relpath, \
                                       self.db.exif_date_digitized, \
                                       self.db.rating, self.db.tags])
        else:
            row = ["test %i" % i for i in range(6)]
            data = [row]
            data = numpy.array(data)
        self.data = data
        return data

    
    def _init_main_listview(self):
        data = self._get_data()
        row = data[0]
        N = len(row)
        dtype_list = [str]*N
        self.labels = ['id','filename', 'relpath', 'date', 'rating', 'tags']
        self.main_listview = listview_on_scrolledwindow(data, \
                                                        dtype_list, \
                                                        self.labels)

    def set_main_list_data(self, max_rows=1000):
        data = self._get_data()
        nc, nr = data.shape
        if nc < max_rows:
            self.main_listview.set_data(data)


    def get_unrated_images(self, ratings):
        N = len(ratings)
        unrated_bool = numpy.zeros(N).astype(bool)
        zero_list = ['0','','Unrated','None']

        for item in zero_list:
            curbool = ratings == item
            unrated_bool = unrated_bool | curbool
        return unrated_bool
        

    def build_boolvect(self):
        N = len(self.db.photo_id)
        boolvect = numpy.ones(N).astype(bool)
        force_str_list = ['rating']
        
        for attr, listbox in self.listdict.iteritems():
            selected = listbox.get_selected()
            if selected != []:
                data = getattr(self.db, attr)
                if attr in force_str_list:
                    data = data.astype(str)
                itembool = numpy.zeros(N).astype(bool)
                for item in selected:
                    if attr == 'rating' and item == 'Unrated':
                        curbool = self.get_unrated_images(data)
                    else:
                        curbool = data == item
                    itembool = itembool | curbool
                boolvect = boolvect & itembool
        self.boolvect = boolvect
        return boolvect


    def filter_one_listbox(self, listbox, attr):
        if hasattr(self, 'boolvect'):
            data = getattr(self.db, attr)
            filt_data = data[self.boolvect]
            unique_filt = numpy.unique(filt_data)
            if attr == 'rating':
                myfilt = unique_filt.astype(str)
                mylist = myfilt.tolist()
                if '0' in mylist:
                    ind = mylist.index('0')
                    mylist[ind] = 'Unrated'
                    unique_filt = mylist
            listbox.set_items(unique_filt)
            

    def filter_listboxes(self):
        """Filter any listboxes that don't have any items selected."""
        for attr, listbox in self.listdict.iteritems():
            selected = listbox.get_selected()
            if not selected:
                self.filter_one_listbox(listbox, attr)
                      

    def _update_filtered_data(self):
        boolvect = self.build_boolvect()
        data = self._get_data()
        #self.filtered_data = numpy.ma.masked_array(data, mask=boolvect)
        self.filtered_data = data[boolvect]


    def _upate_total_filtered(self):
        nr, nc = self.filtered_data.shape
        self.num_found_entry.set_text('%i' % nr)
        
        
    def on_filter_button(self, *args, **kwargs):
        #this method needs to call another method that builds the
        #boolvect from the listboxes and any other relavant criterion
        #boolvect = self.db.year == 2010
        self.filter_data()
        self._upate_total_filtered()


    def map_data_to_db_alldata(self, widget, data=None):
        #print('in map_data_to_db_alldata')
        if data is None:
            data = self.filtered_data
            
        colmap = {'id':'photo_id','filename':'filename', \
                  'relpath':'relpath','date':'exif_date_digitized', \
                  'rating':'rating','tags':'tags'}
        #self.labels = ['id','filename', 'relpath', , 'rating', 'tags']
        self.db.map_data_to_alldata(data, self.labels, colmap)
        self.db.save()



    def build_full_paths(self):
        if hasattr(self,'filtered_data'):
            filenames = self.filtered_data[:,1]
            folder_relpaths = self.filtered_data[:,2]
            fullpaths = []
            thumbpaths = []
            screensizepaths = []
            for name, folder in zip(filenames, folder_relpaths):
                folder_path = os.path.join(myroot, folder)
                thumb_folder = os.path.join(folder_path, 'thumbnails')
                screesize_folder = os.path.join(folder_path, '900by600')
                fp = os.path.join(folder_path, name)
                thmp = os.path.join(thumb_folder, name)
                ssp = os.path.join(screesize_folder, name)
                fullpaths.append(fp)
                thumbpaths.append(thmp)
                screensizepaths.append(ssp)
                if not os.path.exists(thmp):
                    print('did not find thumbnail: %s' % thmp)
            self.screensizepaths = screensizepaths
            self.fullpaths = fullpaths
            self.thumbpaths = thumbpaths
                
                

    def on_load_thumbs_button(self, *args, **kwargs):
        #print('in on_load_thumbs_button method')
        self.build_full_paths()
        self.thumbs_viewer.set_from_paths(self.thumbpaths)
        

    def on_unfilter_button(self, *args, **kwargs):
        #work backwards through the list clearing one for each call,
        #find the first one that has a selection
        backwards_list = [self.rating_listbox, \
                          self.folder_listbox, \
                          self.month_listbox, \
                          self.year_listbox]

        self.revese_listdict = dict((v,k) for k, v in self.listdict.iteritems())

        for listbox in backwards_list:
            selected = listbox.get_selected()
            if selected != []:
                attr = self.revese_listdict[listbox]
                listbox.clear_selected()
                #this almost works, but self.filtered_data needs to be reset
                self.filter_data(filter_boxes=False)
                self._upate_total_filtered()
                self.filter_one_listbox(listbox, attr)
                break
        #I need a method that unfilters one listbox
        #self.filter_listboxes()
        #self.init_listboxes(filter=True)


    def get_selected_photo_ids(self):
        inds = self.thumbs_viewer.get_selected_inds()
        photo_ids = self.filtered_data[inds,0]
        #print('photo_ids = ' + str(photo_ids))
        return photo_ids


    def display_rating(self, rating):
        ## active_radio = self.ratings_radio_list[rating]
        ## active_radio.set_active(True)
        ## self.radio_active = True
        self.ratings_entry.set_text("%s" % rating)


    def _clean_path_for_title(self, pathin):
        droplist =['thumbnails','900by600']
        folder1, filename = os.path.split(pathin)
        folder2, temp = os.path.split(folder1)
        if temp in droplist:
            pathout = os.path.join(folder2, filename)
        else:
            pathout = pathin
        return pathout
    
            
    def update_title(self):
        N = self.thumbs_viewer.get_N()
        inds = self.thumbs_viewer.get_selected_inds()
        i = inds[-1] + 1
        paths = self.thumbs_viewer.get_selections()
        curpath = paths[-1]
        folder, name = os.path.split(curpath)
        mytitle = '%s (%s/%s)' % (name, i, N)
        self.window.set_title(self._clean_path_for_title(curpath))
        self.status_bar.pop(self.cid)
        self.status_bar.push(self.cid, mytitle)


    def on_thumb_selected(self, *args, **kwargs):
        print('in on_thumb_selected')
        self.radio_active = False
        paths = self.thumbs_viewer.get_selections()
        if not paths:
            #print('no paths returned')#<-- when the selection is
                                      #cleared, this method gets
                                      #triggered, but there are no
                                      #paths selected (temporarily)
            return
        screensize_path = thumbpath_to_screensize(paths[-1])
        self.image_on_sw.set_from_path(screensize_path)
        self.notebook.set_current_page(0)
        photo_ids = self.get_selected_photo_ids()
        rating = self.get_filtered_attr(photo_ids[-1], 'rating')
        rating = int(float(rating))
        self.display_rating(rating)
        self.update_title()
        

    def filter_data(self, filter_boxes=True, mymax=1000):#, boolvect):
        self._update_filtered_data()
        nr, nc = self.filtered_data.shape
        if nr < mymax:
            self.main_listview.set_data(self.filtered_data)
        if filter_boxes:
            self.filter_listboxes()


    def get_filtered_row_ind(self, photo_id):
        ids = self.filtered_data[:,0]
        boolvect = ids == photo_id
        N = len(ids)
        ind_array = numpy.arange(N)
        inds = ind_array[boolvect]
        assert len(inds) == 1, 'did not find exactly one match for ' + \
               str(photo_id) + ', inds = ' + str(inds)
        return inds[0]


    def set_filtered_attr(self, photo_id, attr, val):
        row = self.get_filtered_row_ind(photo_id)
        col = self.labels.index(attr)
        self.filtered_data[row, col] = str(val)


    def get_filtered_attr(self, photo_id, attr):
        row = self.get_filtered_row_ind(photo_id)
        col = self.labels.index(attr)
        return self.filtered_data[row, col]


    def check_rating_changed(self, photo_id, new_rating):
        cur_rating = self.get_filtered_attr(photo_id, 'rating')
        print('cur_rating = ' + str(cur_rating))
        print('new_rating = ' + str(new_rating))
        return bool(cur_rating == new_rating)


    def update_main_listview(self):
        data = self._get_data()
        
        #self.main_listview.data = data
        #self.main_listview.set_data(data)


    def delete_one_photo(self, photo_id):
        pdb.set_trace()
        dbrow = self.db.copy_row_by_photo_id(photo_id)
        

    def update_one_rating(self, photo_id, rating):
        print('in update_one_rating')
        #print('photo_id = ' + str(photo_id))
        #print('rating = ' + str(rating))
        match_iter = self.main_listview.find_row_by_photo_id(photo_id)
        self.main_listview.model[match_iter][-2] = rating
        self.db.update_attr(photo_id, 'rating', rating)
        
        

    ## def on_ratings_toggle(self, widget, data, *args, **kwargs):
    ##     print('in on_ratings_toggle,')
    ##     print('data = ' + str(data))
    ##     print('args = ' + str(args))
    ##     print('kwargs = ' + str(kwargs))

    def set_zero_stars(self, *args, **kwargs):
        self.set_rating(0)


    def set_one_star(self, *args, **kwargs):
        self.set_rating(1)


    def set_two_stars(self, *args, **kwargs):
        self.set_rating(2)


    def set_three_stars(self, *args, **kwargs):
        self.set_rating(3)


    def set_four_stars(self, *args, **kwargs):
        self.set_rating(4)


    def set_five_stars(self, *args, **kwargs):
        self.set_rating(5)


    def set_rating(self, rating):
        print('in set_rating, rating = %i' % rating)
        #If a rating is changed, I need to map the changes back into
        #self.db.alldata so that they can be saved.  I need to find
        #the row of alldata based on the photo_id and then find the
        #column based on attr and self.db.labels.

        photo_ids = self.get_selected_photo_ids()
        #print('photo_ids = ' + str(photo_ids))
        for photo_id in photo_ids:
            self.set_filtered_attr(photo_id, 'rating', rating)
            ind = self.get_filtered_row_ind(photo_id)
            self.update_one_rating(photo_id, rating)

        if rating == 0:
            disp = "Unrated"
        else:
            disp = rating
        self.display_rating(disp)


    ## def on_ratings_radio(self, widget, data, *args, **kwargs):
    ##     print('in on_ratings_radio')
    ##     if not self.radio_active:
    ##         print('not active')
    ##         return
    ##     print('active')
    ##     #If a rating is changed, I need to map the changes back into
    ##     #self.db.alldata so that they can be saved.  I need to find
    ##     #the row of alldata based on the photo_id and then find the
    ##     #column based on attr and self.db.labels.
        
    ##     ## print('in on_ratings_radio,')
    ##     ## print('data = ' + str(data))
    ##     ## print('args = ' + str(args))
    ##     ## print('kwargs = ' + str(kwargs))
    ##     photo_ids = self.get_selected_photo_ids()
    ##     #print('photo_ids = ' + str(photo_ids))
    ##     for photo_id in photo_ids:
    ##         #if self.check_rating_changed(photo_id, data):
    ##         #print('rating actually changed')
    ##         self.set_filtered_attr(photo_id, 'rating', data)
    ##         ind = self.get_filtered_row_ind(photo_id)
    ##         self.update_one_rating(photo_id, data)
    ##         #print('ind = ' + str(ind))
    ##         #print('row = ' + str(self.filtered_data[ind]))

            
        
        

        
    def init_listboxes(self, filter=False):
        years = self.find_all_years(filter=filter)
        months = self.find_all_months(filter=filter)
        folders = self.find_all_folders(filter=filter)
        self.year_listbox.set_items(years)
        self.month_listbox.set_items(months)
        self.folder_listbox.set_items(folders)
        ratings = ['Unrated','1','2','3','4','5']
        self.rating_listbox.set_items(ratings)

        
        
    def init_browsing(self, filter=False):
        self.init_listboxes(filter=filter)
        self.set_main_list_data()
        #self.year_combobox.get_model().clear()
        #for elem in years:
        #    self.year_combobox.append_text(str(elem))
        #self.year_combobox.set_active(0)


    def speficify_db_file(self, widget, data=None):
        self.save(settings_path)
        db_name = csv_open_dialog()
        if db_name is not None:
            db_path = os.path.abspath(db_name)
            self.database_path = db_path
            if os.path.exists(db_path):
                self.load_db()
        #print "in speficify_db_file, db_name=%s" % db_name


    def on_item_activated(self, widget):

        ## model = widget.get_model()
        ## path = model[item][COL_PATH]
        ## isDir = model[item][COL_IS_DIRECTORY]

        inds = self.icon_view.get_selected_items()
        model = self.icon_view.get_model()
        
        #print('-'*15)

        for ind in inds:
            #print('ind = %s' % ind)#<-- ind seems to be one tuple of (ind,)
            data = model[ind]#[COL_PATH]#<-- the paths don't really seem to
                                        #    be in the data
            #print('data = %s' % data)
            #pdb.set_trace()
            
    
    def delete_event(self, widget, event, data=None):
        # If you return FALSE in the "delete_event" signal handler,
        # GTK will emit the "destroy" signal. Returning TRUE means
        # you don't want the window to be destroyed.
        # This is useful for popping up 'are you sure you want to quit?'
        # type dialogs.
        print "delete event occurred"

        # Change FALSE to TRUE and the main window will not be destroyed
        # with a "delete_event".
        return False


    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        self.save(settings_path)
        gtk.main_quit()


    def __init__(self):
        # create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)


        self.ui = """<ui>
        <menubar name="MenuBar">
          <menu action="File">
            <menuitem action="Save Database"/>
            <menuitem action="Quit"/>
            <menuitem action="Add Directory to database"/>
          </menu>
          <menu action="Preferences">
            <menuitem action="Specify database file"/>
          </menu>
          <menu action="Rating">
            <menuitem action="Unrated (0 Stars)"/>
            <menuitem action="1 Star"/>
            <menuitem action="2 Stars"/>
            <menuitem action="3 Stars"/>
            <menuitem action="4 Stars"/>
            <menuitem action="5 Stars"/>
          </menu>
        </menubar>
        </ui>"""


        uimanager = gtk.UIManager()

        # Add the accelerator group to the toplevel window
        self.accelg = uimanager.get_accel_group()
        self.window.add_accel_group(self.accelg)

        actiongroup = gtk.ActionGroup('UIManagerExample')
        self.actiongroup = actiongroup

        # Create a ToggleAction, etc.
        actiongroup.add_actions([('Save Database', None, '_Save Database',
                                 '<control>s', 'Save Database', self.map_data_to_db_alldata),
                                 ('Quit', gtk.STOCK_QUIT, '_Quit', None,
                                  'Quit the Program', self.destroy),
                                 ('Add Directory to database', None, 'Add _Directory to database',
                                  '<alt>d', 'Add Directory to database', self.add_directory),
                                 ('File', None, '_File'),
                                 ('Specify database file', None, 'Specify database file',
                                  '<alt>f', 'Specify database file', self.speficify_db_file),
                                 ('Preferences', None, '_Preferences'),
                                 ('Rating', None, '_Rating'),
                                 ('Unrated (0 Stars)', None, 'Unrated (0 Stars)',
                                  '0', 'Unrated (0 Stars)', self.set_zero_stars),
                                 ('1 Star', None, '1 Star',
                                  '1', '1 Star', self.set_one_star),
                                 ('2 Stars', None, '2 Stars',
                                  '2', '2 Stars', self.set_two_stars),
                                 ('3 Stars', None, '3 Stars',
                                  '3', '3 Stars', self.set_three_stars),
                                 ('4 Stars', None, '4 Stars',
                                  '4', '4 Stars', self.set_four_stars),
                                 ('5 Stars', None, '5 Stars',
                                  '5', '5 Stars', self.set_five_stars),
                                 ])
        actiongroup.get_action('Quit').set_property('short-label', '_Quit')
        #actiongroup.get_action('Quit').set_property('short-label', '_Quit')

        uimanager.insert_action_group(actiongroup, 0)
        # Add a UI description
        uimanager.add_ui_from_string(self.ui)

        # Create a MenuBar

        # When the window is given the "delete_event" signal (this is given
        # by the window manager, usually by the "close" option, or on the
        # titlebar), we ask it to call the delete_event () function
        # as defined above. The data passed to the callback
        # function is NULL and is ignored in the callback function.
        self.window.connect("delete_event", self.delete_event)
    
        # Here we connect the "destroy" event to a signal handler.  
        # This event occurs when we call gtk_widget_destroy() on the window,
        # or if we return FALSE in the "delete_event" callback.
        self.window.connect("destroy", self.destroy)
    
        # Sets the border width of the window.
        self.window.set_border_width(2)

        ## self.store = gtk.ListStore(gtk.gdk.Pixbuf)
        ## self.icon_view = gtk.IconView(self.store)
        ## self.icon_view.set_pixbuf_column(0)
        ## self.icon_view.set_selection_mode(gtk.SELECTION_MULTIPLE)

        ## self.folder = '/mnt/personal/pictures/Joshua_Ryan/2011/Mar_2011/Eli/thumbnails/'
        ## self.pat = os.path.join(self.folder, '*.jpg')
        ## self.thumbnail_paths = glob.glob(self.pat)
        ## self.thumbnail_paths.sort()
        
        ## for arg in self.thumbnail_paths:
        ##     pixbuf = gtk.gdk.pixbuf_new_from_file(arg)
        ##     self.store.append((pixbuf, ))

        ## self.sw = gtk.ScrolledWindow()
        
        ## self.icon_view.connect("selection-changed", self.on_item_activated)

        ## self.sw.add(self.icon_view)

        self.main_vbox = gtk.VBox(homogeneous=False, spacing=0)

        self.menubar = uimanager.get_widget('/MenuBar')
        self.main_vbox.pack_start(self.menubar, False)

        self.hpaned = gtk.HPaned()
        self.main_vbox.pack_start(self.hpaned, True)
        self.hpaned.show()

        # Now create the contents of the two halves of the window
        self.thumbs_viewer = thumbnail_viewer.thumbnail_iconview_on_scrollwindow(parent_selection_method=self.on_thumb_selected)
        self.thumbs_viewer.set_size_request(440,-1)
        self.image_on_sw = image_on_scrolled_window.image_on_scrolled_window()
        self.hpaned.add1(self.thumbs_viewer)
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_TOP)
        main_label = gtk.Label("Main")
        self.notebook.append_page(self.image_on_sw, main_label)
        self.image_on_sw.show()
        
        self.thumbs_viewer.show()
        #self.thumbs_viewer.connect("selection-changed", self.on_thumb_selected)

        self.hpaned.add2(self.notebook)
        #self.notebook.show()


        #create search page
        search_window = gtk.ScrolledWindow()
        search_window.set_border_width(2)

        # the policy is one of POLICY AUTOMATIC, or POLICY_ALWAYS.
        # POLICY_AUTOMATIC will automatically decide whether you need
        # scrollbars, whereas POLICY_ALWAYS will always leave the scrollbars
        # there. The first one is the horizontal scrollbar, the second, the
        # vertical.
        search_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        ######################################################
        #
        # This is the creation of the search tab page
        #
        ######################################################
        search_vbox = gtk.VBox(homogeneous=False, spacing=2)
        search_hbox1 = gtk.HBox(homogeneous=False, spacing=2)
        #self.year_combobox = gtk.combo_box_new_text()
        #search_vbox.pack_start(self.year_combobox, False)
        #self.year_listbox = listbox.listbox(label='Years')
        myw = 100
        myh = 150
        myw2 = 250
        
        self.year_listbox = listbox.listbox_on_scrollwindow(label='Years', \
                                                            dtype=int)
        search_hbox1.pack_start(self.year_listbox, False)
        self.year_listbox.set_size_request(myw, myh)
        self.year_listbox.show()
        
        self.month_listbox = listbox.listbox_on_scrollwindow(label='Months')
        search_hbox1.pack_start(self.month_listbox, False)
        self.month_listbox.set_size_request(myw, myh)
        self.month_listbox.show()


        self.folder_listbox = listbox.listbox_on_scrollwindow(label='Folders')
        search_hbox1.pack_start(self.folder_listbox, False)
        self.folder_listbox.set_size_request(myw2, myh)
        self.folder_listbox.show()


        self.rating_listbox = listbox.listbox_on_scrollwindow(label='Ratings')
        search_hbox1.pack_start(self.rating_listbox, False)
        self.rating_listbox.set_size_request(myw2, myh)
        self.rating_listbox.show()


        self.listdict = {'year':self.year_listbox, \
                         'month':self.month_listbox, \
                         'folder_name':self.folder_listbox, \
                         'rating':self.rating_listbox, \
                         }


        search_vbox.pack_start(search_hbox1, False, False)

        #middle button box
        arg1 = False
        arg2 = True
        search_buttons_hbox = gtk.HBox(homogeneous=False, spacing=2)
        self.filter_button = gtk.Button(label="Filter")
        self.filter_button.connect("clicked", self.on_filter_button, None)
        self.filter_button.add_accelerator("clicked", self.accelg, ord("f"), \
                                           gtk.gdk.CONTROL_MASK, \
                                           accel_flags=gtk.ACCEL_VISIBLE)

        self.unfilter_button = gtk.Button(label="Unfilter")
        self.unfilter_button.connect("clicked", self.on_unfilter_button, None)
        self.unfilter_button.add_accelerator("clicked", self.accelg, ord("u"), \
                                             gtk.gdk.CONTROL_MASK, \
                                             accel_flags=gtk.ACCEL_VISIBLE)
        
        #pack_start(widget, expand, fill, padding
        search_buttons_hbox.pack_start(self.filter_button, arg1, False)
        search_buttons_hbox.pack_start(self.unfilter_button, arg1, False)

        number_label = gtk.Label("Images Found:")
        Entry_width = 100
        self.num_found_entry = gtk.Entry()
        self.num_found_entry.set_max_length(10)
        self.num_found_entry.set_text("")
        self.num_found_entry.set_size_request(Entry_width,-1)
        self.num_found_entry.set_alignment(0.95)
        misc_hbox = gtk.HBox(False, 0)
        misc_hbox.pack_start(number_label, False)
        misc_hbox.pack_start(self.num_found_entry, False)
        search_buttons_hbox.pack_start(misc_hbox, arg1, False, 5)

        self.load_thumbs_button = gtk.Button(label="Load Thumbnails")
        self.load_thumbs_button.connect("clicked", self.on_load_thumbs_button, None)
        self.load_thumbs_button.add_accelerator("clicked", self.accelg, ord("l"), \
                                                gtk.gdk.CONTROL_MASK, \
                                                accel_flags=gtk.ACCEL_VISIBLE)
        
        #pack_start(widget, expand, fill, padding
        search_buttons_hbox.pack_start(self.load_thumbs_button, arg1, False)
        
        search_vbox.pack_start(search_buttons_hbox, False)

        #Need the main DB ListStore and TreeView here
        self._init_main_listview()
        search_vbox.pack_start(self.main_listview, True, True)

        search_hbox = gtk.HBox(homogeneous=False, spacing=0)
        search_hbox.pack_start(search_vbox, True, True)

        search_label = gtk.Label("Search")
        self.notebook.append_page(search_hbox, search_label)
        search_window.show()
        
        ######################################################
        #
        # End search tab page
        #
        ######################################################
    
        #bottom toolbar
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        self.toolbar.set_style(gtk.TOOLBAR_BOTH)
        self.toolbar.set_border_width(5)
        tool_hbox = gtk.HBox(False, 0)
        tool_hbox.pack_start(self.toolbar, True, True)

        iconp = gtk.Image() # icon widget
        iconp.set_from_file("prev_arrow.png")
        self.prev_button = gtk.ToolButton(icon_widget=iconp, label="Previous")
        self.prev_button.show()
        self.toolbar.insert(self.prev_button, 0)
        self.prev_button.connect("clicked", self.prev_image_method, None)
        self.prev_button.add_accelerator("clicked", self.accelg, ord("p"), \
                                         0, \
                                         accel_flags=gtk.ACCEL_VISIBLE)

        iconn = gtk.Image() # icon widget
        iconn.set_from_file("next_arrow.png")
        self.next_button = gtk.ToolButton(icon_widget=iconn, label="Next")
        self.next_button.show()
        self.toolbar.insert(self.next_button, -1)
        self.next_button.connect("clicked", self.next_image_method, None)
        self.next_button.add_accelerator("clicked", self.accelg, ord("n"), \
                                         0, \
                                         accel_flags=gtk.ACCEL_VISIBLE)

        icond = gtk.Image() # icon widget
        icond.set_from_file("delete_icon.png")
        self.delete_button = gtk.ToolButton(icon_widget=icond, label="Delete")
        self.delete_button.show()
        self.toolbar.insert(self.delete_button, -1)
        self.delete_button.connect("clicked", self.on_delete_button, None)


        self.delete_button.add_accelerator("clicked", self.accelg, ord("d"), \
                                           gtk.gdk.CONTROL_MASK, \
                                           accel_flags=gtk.ACCEL_VISIBLE)

        #Ratings
        ratings_label = gtk.Label("Ratings (stars)")
        ratings_vbox = gtk.VBox(False, 0)
        ratings_vbox.pack_start(ratings_label, False)
        self.ratings_entry = gtk.Entry()
        self.ratings_entry.set_max_length(9)
        self.ratings_entry.set_text("")
        self.ratings_entry.set_alignment(0.5)
        Entry_width = 50
        self.ratings_entry.set_size_request(Entry_width,-1)
        ratings_vbox.pack_start(self.ratings_entry, False)
        #ratings_hbox = gtk.HBox(False, 0)
        ## self.no_stars_radio = gtk.RadioButton(label='Unrated')
        ## self.one_star_radio = gtk.RadioButton(group=self.no_stars_radio,
        ##                                       label='1')        
        ## self.two_stars_radio = gtk.RadioButton(group=self.no_stars_radio, \
        ##                                        label='2')
        ## self.three_stars_radio = gtk.RadioButton(group=self.no_stars_radio, \
        ##                                          label='3')
        ## self.four_stars_radio = gtk.RadioButton(group=self.no_stars_radio, \
        ##                                         label='4')
        ## self.five_stars_radio = gtk.RadioButton(group=self.no_stars_radio, \
        ##                                         label='5')
        ## self.ratings_radio_list = [self.no_stars_radio, \
        ##                            self.one_star_radio, \
        ##                            self.two_stars_radio, \
        ##                            self.three_stars_radio, \
        ##                            self.four_stars_radio, \
        ##                            self.five_stars_radio]
        ## for i, radio in enumerate(self.ratings_radio_list):
        ##     ratings_hbox.pack_start(radio, False, 0)
        ##     ## radio.add_accelerator("clicked", self.accelg, ord('%i' % i), \
        ##     ##                       0, \
        ##     ##                       accel_flags=gtk.ACCEL_VISIBLE)
        ##     radio.connect("clicked", self.on_ratings_radio, i)
        ##     #radio.connect("toggled", self.on_ratings_toggle, i)


        self.status_bar = gtk.Statusbar()      
        tool_hbox.pack_start(self.status_bar, False)#True, True, 5)
        self.status_bar.set_size_request(250,-1)
        self.status_bar.show()
        self.cid = self.status_bar.get_context_id("photo_app")
        ## ratings_vbox.pack_start(ratings_hbox, False)
        ratings_vbox2 = gtk.VBox(False, 0)
        ratings_vbox2.pack_start(ratings_vbox, True, False, 5)
        tool_hbox.pack_start(ratings_vbox2, False, False, 5)
        self.main_vbox.pack_start(tool_hbox, False)
        
        #self.toolbar.append_space() # space after item


        #self.toolbar.set_style(gtk.TOOLBAR_ICONS)
        self.toolbar.set_style(gtk.TOOLBAR_BOTH)
        
        
        self.window.add(self.main_vbox)

        self.radio_active = True
        
        self.database_path = None
        self.saveattrs = ['database_path']
        if os.path.exists(settings_path):
            self.load(settings_path)
        #print('self.database_path = %s' % self.database_path)

        if hasattr(self, 'db'):
            self.init_browsing()

        pn1 = self.notebook.get_current_page()
        self.notebook.show()
        self.window.set_size_request(1200,700)
        self.notebook.set_current_page(1)
        pn2 = self.notebook.get_current_page()
        #print('pn1 = %s' % pn1)
        #print('pn2 = %s' % pn2)
        self.window.show_all()
        self.notebook.next_page()
        #print('pn3 = %s' % pn2)

        
    def load(self, filepath):
        rwkmisc.object_that_saves.load(self, filepath)
        if hasattr(self, 'database_path'):
            #print('self.database_path = ' + self.database_path)
            folder, db_name = os.path.split(self.database_path)
            alt_path = os.path.join(myroot, db_name)
            found = 0
            if os.path.exists(self.database_path):
                found = 1
            elif os.path.exists(alt_path):
                self.database_path = alt_path
                found = 1
            if found:
                self.load_db()
                

    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()

# If the program is run directly or passed as an argument to the python
# interpreter then create a HelloWorld instance and show it
if __name__ == "__main__":
    myapp = photo_app()
    myapp.main()
