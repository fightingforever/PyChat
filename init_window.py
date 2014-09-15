#! /usr/bin/python
# -*-  coding=utf8  -*-

#    Copyright (C) 2014 Guangmu Zhu <guangmuzhu@gmail.com>
#
#    This file is part of PyChat.
#
#    PyChat is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    PyChat is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with PyChat.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os

import platform
import gtk.gdk

def main(argv):
    #    win=gtk.gdk.window_foreign_new(gtk.gdk.get_default_root_window().property_get("_NET_ACTIVE_WINDOW")[2][0])
    #    state = win.property_get("_NET_WM_STATE")[2]
    #    maximized='_NET_WM_STATE_MAXIMIZED_HORZ' in state and '_NET_WM_STATE_MAXIMIZED_VERT' in state
    #    if maximized:
    #        win.unmaximize()
    #    if win.get_decorations() == 0 :
    #        win.set_decorations(gtk.gdk.DECOR_ALL)
    #    else:
    #        win.set_decorations(0)
    #    if maximized:
    #        win.maximize()
    #    gtk.gdk.window_process_all_updates()
    
    if platform.platform().find("Ubuntu") != -1 or len(argv) == 0:
        win=gtk.gdk.window_foreign_new(gtk.gdk.get_default_root_window().property_get("_NET_ACTIVE_WINDOW")[2][0])
    else: # Fedora didn't support _NET_ACTIVE_WINDOW well
        win=gtk.gdk.window_foreign_new(int(argv[0]))
    win.set_functions(gtk.gdk.FUNC_MINIMIZE | gtk.gdk.FUNC_MOVE)
    gtk.gdk.window_process_all_updates()

if __name__ == "__main__":
    main(sys.argv[1:])
