# Copyright (c) 2006, Daniel J. Popowich
# 
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Send bug reports and contributions to:
#
#    dpopowich AT astro dot umass dot edu
#
# This version of the file is part of fpdb, contact: fpdb-main@lists.sourceforge.net

'''
TreeViewTooltips.py

Provides TreeViewTooltips, a class which presents tooltips for cells,
columns and rows in a gtk.TreeView.

------------------------------------------------------------
    This file includes a demo.  Just execute the file:

       python TreeViewTooltips.py
------------------------------------------------------------

To use, first subclass TreeViewTooltips and implement the get_tooltip()
method; see below.  Then add any number of gtk.TreeVew widgets to a
TreeViewTooltips instance by calling the add_view() method.  Overview
of the steps:

    # 1. subclass TreeViewTooltips
    class MyTooltips(TreeViewTooltips):

        # 2. overriding get_tooltip()
        def get_tooltip(...):
            ...

    # 3. create an instance
    mytips = MyTooltips()

    # 4. Build up your gtk.TreeView.
    myview = gtk.TreeView()
    ...# create columns, set the model, etc.

    # 5. Add the view to the tooltips
    mytips.add_view(myview)

How it works: the add_view() method connects the TreeView to the
"motion-notify" event with the callback set to a private method.
Whenever the mouse moves across the TreeView the callback will call
get_tooltip() with the following arguments:

    get_tooltip(view, column, path)

where,

    view:   the gtk.TreeView instance. 
    column: the gtk.TreeViewColumn instance that the mouse is
            currently over.
    path:   the path to the row that the mouse is currently over.

Based on whether or not column and path are checked for specific
values, get_tooltip can return tooltips for a cell, column, row or the
whole view:

    Column Checked      Path Checked      Tooltip For...
          Y                 Y             cell
          Y                 N             column
          N                 Y             row
          N                 N             view

get_tooltip() should return None if no tooltip should be displayed.
Otherwise the return value will be coerced to a string (with the str()
builtin) and stripped; if non-empty, the result will be displayed as
the tooltip.  By default, the tooltip popup window will be displayed
centered and just below the pointer and will remain shown until the
pointer leaves the cell (or column, or row, or view, depending on how
get_tooltip() is implemented).

'''


import pygtk
pygtk.require('2.0')

import gtk
import gtk.gdk
import gobject

if gtk.gtk_version < (2, 8):
    import warnings

    msg = (_('''This module was developed and tested with version 2.8.18 of gtk.  You are using version %d.%d.%d.  Your milage may vary.''')
           % gtk.gtk_version)
    warnings.warn(msg)


# major, minor, patch
version = 1, 0, 0

class TreeViewTooltips:

    def __init__(self):
        
        '''
        Initialize the tooltip.  After initialization there are two
        attributes available for advanced control:

            window: the popup window that holds the tooltip text, an
                    instance of gtk.Window.
            label:  a gtk.Label that is packed into the window.  The
                    tooltip text is set in the label with the
                    set_label() method, so the text can be plain or
                    markup text.

        Be default, the tooltip is enabled.  See the enabled/disabled
        methods.
        '''

        # create the window
        self.window = window = gtk.Window(gtk.WINDOW_POPUP)
        window.set_name('gtk-tooltips')
        window.set_resizable(False)
        window.set_border_width(4)
        window.set_app_paintable(True)
        window.connect("expose-event", self.__on_expose_event)


        # create the label
        self.label = label = gtk.Label()
        label.set_line_wrap(True)
        label.set_alignment(0.5, 0.5)
        label.set_use_markup(True)
        label.show()
        window.add(label)

        # by default, the tooltip is enabled
        self.__enabled = True
        # saves the current cell
        self.__save = None
        # the timer id for the next tooltip to be shown
        self.__next = None
        # flag on whether the tooltip window is shown
        self.__shown = False

    def enable(self):
        'Enable the tooltip'
        
        self.__enabled = True
        
    def disable(self):
        'Disable the tooltip'
        
        self.__enabled = False

    def __show(self, tooltip, x, y):

        '''show the tooltip popup with the text/markup given by
        tooltip.

        tooltip: the text/markup for the tooltip.
        x, y:  the coord. (root window based) of the pointer.
        '''

        window = self.window
        
        # set label
        self.label.set_label(tooltip)
        # resize window
        w, h = window.size_request()
        # move the window 
        window.move(*self.location(x,y,w,h))
        # show it
        window.show()
        self.__shown = True

    def __hide(self):
        'hide the tooltip'

        self.__queue_next()
        self.window.hide()
        self.__shown = False

    def __leave_handler(self, view, event):
        'when the pointer leaves the view, hide the tooltip'
        
        self.__hide()

    def __motion_handler(self, view, event):
        'As the pointer moves across the view, show a tooltip.'

        path = view.get_path_at_pos(int(event.x), int(event.y))
        
        if self.__enabled and path:
            path, col, x, y = path
            tooltip = self.get_tooltip(view, col, path)
            if tooltip is not None:
                tooltip = str(tooltip).strip()
                if tooltip:
                    self.__queue_next((path, col), tooltip,
                                      int(event.x_root),
                                      int(event.y_root))
                    return

        self.__hide()

    def __queue_next(self, *args):

        'queue next request to show a tooltip'

        # if args is non-empty it means a request was made to show a
        # tooltip.  if empty, no request is being made, but any
        # pending requests should be cancelled anyway.

        cell = None

        # if called with args, break them out
        if args:
            cell, tooltip, x, y = args

        # if it's the same cell as previously shown, just return
        if self.__save == cell:
            return

        # if we have something queued up, cancel it
        if self.__next:
            gobject.source_remove(self.__next)
            self.__next = None

        # if there was a request...
        if cell:
            # if the tooltip is already shown, show the new one
            # immediately
            if self.__shown:
                self.__show(tooltip, x, y)
            # else queue it up in 1/2 second
            else:
                self.__next = gobject.timeout_add(500, self.__show,
                                                  tooltip, x, y)

        # save this cell
        self.__save = cell


    def __on_expose_event(self, window, event):

        # this magic is required so the window appears with a 1-pixel
        # black border (default gtk Style).  This code is a
        # transliteration of the C implementation of gtk.Tooltips.
        w, h = window.size_request()
        window.style.paint_flat_box(window.window, gtk.STATE_NORMAL,
                                    gtk.SHADOW_OUT, None, window,
                                    'tooltip', 0, 0, w, h)

    def location(self, x, y, w, h):

        '''Given the x,y coordinates of the pointer and the width and
        height (w,h) demensions of the tooltip window, return the x, y
        coordinates of the tooltip window.

        The default location is to center the window on the pointer
        and 4 pixels below it.
        '''

        return x - w/2, y + 4

    def add_view(self, view):

        'add a gtk.TreeView to the tooltip'
        
        assert isinstance(view, gtk.TreeView), \
               ('This handler should only be connected to '
                'instances of gtk.TreeView')

        view.connect("motion-notify-event", self.__motion_handler)
        view.connect("leave-notify-event", self.__leave_handler)

    def get_tooltip(self, view, column, path):
        'See the module doc string for a description of this method'
        
        raise NotImplemented, 'Subclass must implement get_tooltip()'


if __name__ == '__main__':

    ############################################################
    # DEMO
    ############################################################

    # First, subclass TreeViewTooltips

    class DemoTips(TreeViewTooltips):

        def __init__(self, customer_column):
            # customer_column is an instance of gtk.TreeViewColumn and
            # is being used in the gtk.TreeView to show customer names.
            self.cust_col = customer_column

            # call base class init
            TreeViewTooltips.__init__(self)

        def get_tooltip(self, view, column, path):

            # we have a two column view: customer, phone; we'll make
            # tooltips cell-based for the customer column, but generic
            # column-based for the phone column.

            # customer
            if column is self.cust_col:

                # By checking both column and path we have a
                # cell-based tooltip.
                model = view.get_model()
                customer = model[path][2]
                return '<big>%s %s</big>\n<i>%s</i>' % (customer.fname,
                                                        customer.lname,
                                                        customer.notes)
            # phone
            else:
                return ('<big><u>Generic Column Tooltip</u></big>\n'
                        'Unless otherwise noted, all\narea codes are 888')

        def XX_location(self, x, y, w, h):
            # rename me to "location" so I override the base class
            # method.  This will demonstrate being able to change
            # where the tooltip window popups, relative to the
            # pointer.

            # this will place the tooltip above and to the right
            return x + 10, y - (h + 10)

    # Here's our customer
    class Customer:

        def __init__(self, fname, lname, phone, notes):
            self.fname = fname
            self.lname = lname
            self.phone = phone
            self.notes = notes

    # create a bunch of customers
    customers = []
    for fname, lname, phone, notes in [
        ('Joe', 'Schmoe', '555-1212', 'Likes to Morris dance.'),
        ('Jane', 'Doe', '555-2323',
         'Wonders what the hell\nMorris dancing is.'),
        ('Phred', 'Phantastic', '900-555-1212', 'Dreams of Betty.'),
        ('Betty', 'Boop', '555-3434', 'Dreams in b&amp;w.'),
        ('Red Sox', 'Fan', '555-4545',
         "Still livin' 2004!\nEspecially after 2006.")]:
        customers.append(Customer(fname, lname, phone, notes))

    # Build our model and view
    model = gtk.ListStore(str, str, object)
    for c in customers:
        model.append(['%s %s' % (c.fname, c.lname), c.phone, c])

    view = gtk.TreeView(model)
    view.get_selection().set_mode(gtk.SELECTION_NONE)

    # two columns, name and phone
    cell = gtk.CellRendererText()
    cell.set_property('xpad', 20)
    namecol = gtk.TreeViewColumn('Customer Name', cell, text=0)
    namecol.set_min_width(200)
    view.append_column(namecol)

    cell = gtk.CellRendererText()
    phonecol = gtk.TreeViewColumn('Phone', cell, text=1)
    view.append_column(phonecol)

    # finally, connect the tooltip, specifying the name column as the
    # column we want the tooltip to popup over.
    tips = DemoTips(namecol)
    tips.add_view(view)

    # We're going to demonstrate enable/disable.  First we need a
    # callback function to connect to the toggled signal.
    def toggle(button):
        if button.get_active():
            tips.disable()
        else:
            tips.enable()

    # create a checkbutton and connect our handler
    check = gtk.CheckButton('Check to disable view tooltips')
    check.connect('toggled', toggle)

    # a standard gtk.Tooltips to compare to
    tt = gtk.Tooltips()
    tt.set_tip(check, ('This is a standard gtk tooltip.\n'
                       'Compare me to the tooltips above.'))
    
    # create a VBox to pack the view and checkbutton
    vbox = gtk.VBox()
    vbox.pack_start(view)
    vbox.pack_start(check, False)
    vbox.show_all()
    
    # pack the vbox into a simple dialog and run it
    dialog = gtk.Dialog('TreeViewTooltips Demo')
    close = dialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_NONE)

    # add a tooltip for the close button
    tt.set_tip(close, 'Click to end the demo.')
                              
    dialog.set_default_size(400,400)
    dialog.vbox.pack_start(vbox)
    dialog.run()
