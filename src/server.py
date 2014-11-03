#!/usr/bin/python
"""
    Copyright (C) 2014 Andres Adjimann

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import os
import sys

from server.PyCvStreamerHTTPServer import PyCvSSLHTTPServer
from server.PyCvStreamerHTTPServer import PyCvHTTPServer
from server.PyCvCapture import PyCvCapture


def main():
    t = PyCvCapture.start()

    src_dirname, filename = os.path.split(sys.argv[0])
    dirname, filename = os.path.split( src_dirname )

    routes = {
        10 : { 'regexp': r'^/stream$', 'module': 'server.PyCvCapture', 'controller': 'PyCvCaptureController',
         'action': 'stream_action', 'secure': True, 'no_log' : True},

        11 : {'regexp': r'^/\?action=(.*)$', 'module': 'server.PyCvMjpgStreamerController', 'controller': 'PyCvMjpgStreamerController',
         'action': 'mjpg_streamer_action', 'secure': True, 'no_log' : True},

        12 : {'regexp': r'^/mjpg/(.*)', 'module': 'PyCvFileController', 'controller': 'ContentController',
         'action': 'show_action', 'secure': False, 'file_path': os.path.join(dirname, 'www', 'mjpg')},

        13 : {'regexp': r'^/(.*)$', 'module': 'PyCvFileController', 'controller': 'ContentController',
         'action': 'show_action', 'secure': False, 'file_path': os.path.join(dirname, 'www')},

    }

    tokens = {'adji': 'adji'}

    #server = PyCvSSLHTTPServer(('', 4443), routes, tokens=tokens)
    server = PyCvHTTPServer(('',8080),routes)
    try:
        print "server started"
        server.serve_forever()
    except KeyboardInterrupt:
        print "waiting for server"
        server.shutdown()
        print "waiting for camera"
        PyCvCapture.shutdown()
        print "done"


if __name__ == '__main__':
    main()
