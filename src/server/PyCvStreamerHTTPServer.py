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
import socket
import ssl
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import re


class PyCvStreamerController(object):
    def __init__(self, handler):
        self.__handler = handler

    @property
    def handler(self):
        return self.__handler


class PyCvStreamerRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.route = False
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    #override
    def log_request(self, code='-', size='-'):
        if self.route and 'no_log' in self.route and self.route['no_log']:
            return
        self.log_message('"%s" %s %s',
                         self.requestline, str(code), str(size))

    def send_message(self, txt):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write('<html><head></head><body>')
        self.wfile.write(txt)
        self.wfile.write('</body></html>')

    def do_route(self):
        #print "Routing : ", self.command, " -> ", self.path
        cls = self.compiled_route['cls']
        if not self.route['action'] in cls.__dict__:
            self.send_error(500, 'Invalid action ' + self.route['class'].__name__ + '.' + self.route['action'])
            return

        rest = self.path[self.match.pos:]
        i = rest.rfind('?')
        if i >= 0:
            rest, query = rest[:i], rest[i + 1:]
        else:
            query = ''
        decoded_query = query.replace('+', ' ')
        args = []
        if '=' not in decoded_query:
            args.append(decoded_query)

        func = cls.__dict__[self.route['action']]
        obj = cls(self)
        apply(func, (obj,))

    def apply_route(self):
        ret = self.server.get_compiled_route(self.path)
        if not ret:
            # Not found
            self.send_error(404, "Route not found for command " + self.command + " path " + self.path)
            return

        ( self.match, self.compiled_route ) = ret
        self.route = self.compiled_route['route']
        if not 'secure' in self.route or not self.route['secure'] or not self.server.is_secure:
            self.do_route()
            return

        authorization = self.headers.getheader("authorization")
        if not authorization:
            self.auth_header()
            self.wfile.write('no auth header received'.encode('UTF-8'))
            return

        auth_type = None
        remote_user = None
        remote_pass = None
        authorization = authorization.split()
        if len(authorization) == 2:
            import base64, binascii

            auth_type = authorization[0]
            if authorization[0].lower() == "basic":
                try:
                    authorization = base64.decodestring(authorization[1])
                except binascii.Error:
                    pass
                else:
                    authorization = authorization.split(':')
                    if len(authorization) == 2:
                        remote_user = authorization[0]
                        remote_pass = authorization[1]

        if auth_type.lower() != 'basic':
            self.simple_page("Only basic auth allowed")
            return

        if remote_user not in self.server.tokens or remote_pass != self.server.tokens[remote_user]:
            self.auth_header()
            self.wfile.write(self.headers['Authorization'].encode('UTF-8'))
            self.wfile.write(' not authenticated'.encode('UTF-8'))
            return
        # authenticated
        self.do_route()

    def auth_header(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Cam login\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_POST(self):
        self.apply_route()

    def do_GET(self):
        self.apply_route()


class PyCvHTTPServer(ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, routes={}, bind_and_activate=True, is_secure=False, tokens={}):
        self.tokens = tokens
        self.is_secure = is_secure;
        self.cancel = False
        self.compiled_routes = {}
        for k in routes.keys():
            self.add_route(k, routes[ k ])
        HTTPServer.__init__(self, server_address, PyCvStreamerRequestHandler, bind_and_activate=bind_and_activate)

    def add_route(self, key, route):
        regexp = route['regexp']
        module = route['module']
        controller = route['controller']
        m = __import__(module, globals(), locals(), [controller], -1)
        cls = getattr(m, controller)
        print "adding route : ", m, " class ", controller
        self.compiled_routes[key] = {'cls': cls, 'mod': m, 're': re.compile(regexp), 'route': route}

    def get_compiled_route(self, path):
        for k in sorted(self.compiled_routes.keys()):
            match = self.compiled_routes[k]['re'].search(path)
            if match:
                return ( match, self.compiled_routes[k] )
        return False


    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        try:
            self.RequestHandlerClass(request, client_address, self)
        except socket.error, e:  # broken pipe
            pass

    def shutdown(self):
        self.cancel = True
        HTTPServer.shutdown(self)


class PyCvSSLHTTPServer(PyCvHTTPServer):
    def __init__(self, server_address, routes={}, fpem='server.pem', tokens={}, is_secure=True):
        PyCvHTTPServer.__init__(self, server_address, routes, bind_and_activate=False, is_secure=is_secure,
                                tokens=tokens)
        self.socket = ssl.wrap_socket(self.socket, certfile=fpem, server_side=True)
        self.server_bind()
        self.server_activate()

