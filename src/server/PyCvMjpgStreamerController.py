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
__author__ = 'adji'

import socket
import time

from PyCvStreamerHTTPServer import PyCvStreamerController
from PyCvCapture import PyCvCapture


class PyCvMjpgStreamerController(PyCvStreamerController):

    def send_std_header(self):
        self.handler.send_response(200)
        self.handler.send_header('Connection', "close")
        self.handler.send_header('Pragma', "no-cache")
        self.handler.send_header('Cache-Control', "no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0")
        self.handler.send_header('Expires', 'Mon, 3 Jan 2000 12:34:56 GMT' )


    def mjpg_streamer_action(self):
        action = self.handler.match.group(1)
        if action.startswith('snapshot'):
            tmp_file = PyCvCapture.read()
            if tmp_file is not None:
                self.send_std_header()
                self.handler.send_header('Content-Type', 'image/jpeg')
                self.handler.send_header('Content-Length', str(tmp_file.len))
                self.handler.end_headers()
                self.handler.wfile.write(tmp_file.getvalue())
        elif action.startswith('command&command='):
            cmd = action[16:]
            print cmd
            self.handler.send_response(200)
            self.handler.end_headers()
            self.handler.wfile.write("OK (ignored)")
        elif action == 'stream':
            self.send_std_header()
            self.handler.send_header('Content-Type', 'multipart/x-mixed-replace;boundary=--jpgboundary')
            self.handler.end_headers()
            while not self.handler.server.cancel:
                try:
                    tmp_file = PyCvCapture.read()
                    if tmp_file is not None:
                        self.handler.wfile.write("--jpgboundary\r\n")
                        self.handler.send_header('Content-Type', 'image/jpeg')
                        self.handler.send_header('Content-Length', str(tmp_file.len))
                        self.handler.end_headers()
                        self.handler.wfile.write(tmp_file.getvalue())
                        self.handler.end_headers()
                        self.handler.wfile.flush()
                    time.sleep(0.05)
                except KeyboardInterrupt:
                    break
                except socket.error, e:
                    break
        else:
            self.handler.send_error(404, "File not found")

    def index_action(self):
        self.handler.server.add_route(
            {'regexp': r'^/image/', 'module': 'server.PyCvCapture', 'controller': 'PyCvCaptureController',
             'action': 'stream_action', 'secure': True})

        self.handler.send_message('<img src="image/cam.mjpg"/>')

