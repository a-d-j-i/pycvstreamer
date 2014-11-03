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
import cv2
import Image
import StringIO
import threading
import time

from PyCvStreamerHTTPServer import PyCvStreamerController


class PyCvCaptureInstance():
    def __init__(self):
        self.thread = threading.Thread(target=self.run)
        self.lastImg = None
        self.lock = threading.Lock()
        self.cancel = False

    def start(self):
        self.thread.start()

    def run(self):
        capture = cv2.VideoCapture(0)
#        capture.set(3, 320);
#        capture.set(4, 240);
#        capture.set(12, 0.2);
        while not self.cancel:
            rc, img = capture.read()
            if not rc:
                print 'Frame not captured'
                time.sleep(0.5)
                continue
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            jpg = Image.fromarray(img_rgb)
            tmp_file = StringIO.StringIO()
            jpg.save(tmp_file, 'JPEG')
            self.lock.acquire()
            try:
                self.lastImg = tmp_file
            finally:
                self.lock.release()
            time.sleep(0.05)
        print "camera thread done start"
        capture.release()
        print "camera thread done"

    def read(self):
        self.lock.acquire()
        try:
            return self.lastImg
        finally:
            self.lock.release()

    def shutdown(self):
        self.cancel = True
        self.thread.join()


PyCvCapture = PyCvCaptureInstance()


class PyCvCaptureController(PyCvStreamerController):
    def stream_action(self):
        self.handler.send_response(200)
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

    def index_action(self):
        self.handler.server.add_route(0, {'regexp': r'^/image/', 'module': 'server.PyCvCapture',
                                          'controller': 'PyCvCaptureController',
                                          'action': 'stream_action', 'secure': True})

        self.handler.send_message('<img src="image/cam.mjpg"/>')

