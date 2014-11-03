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
import os
import mimetypes
import posixpath
import shutil
import stat

from PyCvStreamerHTTPServer import PyCvStreamerController


class ContentController(PyCvStreamerController):
    CONTENT_BASE_PATH = 'public/'

    def show_action(self):
        f = self.send_head()
        if f:
            shutil.copyfileobj(f, self.handler.wfile)
            f.close()

    def send_head(self):
        filename = os.path.join(self.handler.route['file_path'], self.handler.match.group(1))
        try:
            fs = os.stat(filename)
            if stat.S_ISDIR(fs.st_mode):
                filename = os.path.join(filename, 'index.html')
                fs = os.stat(filename)
            ctype = self.guess_type(filename)
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(filename, 'rb')
        except OSError:
            self.handler.send_error(404, "File not found : " + filename)
            return False
        except IOError:
            self.handler.send_error(404, "File not found : " + filename)
            return False
        self.handler.send_response(200)
        self.handler.send_header("Content-type", ctype)
        self.handler.send_header("Content-Length", str(fs[6]))
        self.handler.send_header("Last-Modified", self.handler.date_time_string(fs.st_mtime))
        self.handler.end_headers()
        return f

        """if os.access(filename, os.R_OK) and not os.path.isdir(filename):
            # TODO: is there any possibility to access files outside the root with ..?
            file = open(filename, "r")
            content = file.read()
            file.close()

            #TODO: set correct content type
            self.handler.send_response(200)
            self.handler.send_header('Content-type', 'text/html')
            self.handler.end_headers()
            self.handler.wfile.write(content)
        else:
            self.handler.send_response(404)
            self.handler.end_headers()"""

    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init()  # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream',  # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        '.jar': 'application/java-archive',
        ".html": "text/html",
        '.htm':  "text/html",
        '.css':  "text/css",
        '.jsv':   "text/javascript",
        '.txt':  "text/plain",
        '.jpg':  "image/jpeg",
        '.jpeg': "image/jpeg",
        '.png':  "image/png",
        '.gif':  "image/gif",
        '.ico':  "image/x-icon",
        '.swf':  "application/x-shockwave-flash",
        '.cab':  "application/x-shockwave-flash",
        '.jar':  "application/java-archive",
    })
