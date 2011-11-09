#! /usr/bin/env python
# -*- coding: utf-8 *-*

#  Copyright (c) 2011 - Nicolas Bareil (nico AT chdir.org)
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
#  02110-1301 USA.


from twisted.web import proxy, http
from twisted.internet import reactor

from optparse import OptionParser
import sys

class LoggingProxyClient(proxy.ProxyClient):
    def handleHeader(self, key, value):
        global out
        out.write('<<< %s %s\n' % (key, value))
        proxy.ProxyClient.handleHeader(self, key, value)

    def handleResponsePart(self, buffer):
        global out
        out.write('\n')
        if options.body:
            out.write(repr(buffer) + '\n')
        proxy.ProxyClient.handleResponsePart(self, buffer)

    def finish(self):
        if not self._disconnected:
            return proxy.ProxyClient.finish(self)


class LoggingProxyClientFactory(proxy.ProxyClientFactory):
    protocol = LoggingProxyClient


class LoggingProxyRequest(proxy.ProxyRequest):
    protocols = {'http': LoggingProxyClientFactory}

    def process(self):
        if not self.uri.startswith('http://'):
            # XXX: should do something for https...
            return
        global out
        out.write('>>> %s %s\n' % (self.method, self.path))
        for header,values in self.requestHeaders.getAllRawHeaders():
            for value in values:
                out.write('>>> %s: %s\n' % (header, value))
        out.write('>>>\n')
        for key,values in self.args.items():
            for value in values:
                out.write('>>>    %s: %r\n' % (key, value))
        out.write('>>>\n')
        proxy.ProxyRequest.process(self)


class LoggingProxy(proxy.Proxy):
    requestFactory = LoggingProxyRequest


class ProxyFactory(http.HTTPFactory):
    protocol = LoggingProxy


if __name__ == '__main__':
    parser = OptionParser(usage=u'usage: %prog [options]')

    parser.add_option('-o', '--output', dest='output', metavar='FILE',
                      help='Redirect output')
    parser.add_option('-b', '--body', dest='body', action='store_true', default=False,
                      help='Print response body (can be large!)')
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true', default=False,
                      help='verbose mode')
    parser.add_option('-p', '--port', dest='port', action='store', type='int', default=8080,
                      help='Listening port')
    parser.add_option('-a', '--addr', dest='addr', action='store', 
                      metavar='ADDRESS',default='127.0.0.1',
                      help='Bind address (WARNING: Do not expose this daemon on Internet)')

    (options,args) = parser.parse_args()

    if options.output:
        out = open(options.output, 'w+')
    else:
        out = sys.stdout

    reactor.listenTCP(options.port, ProxyFactory(), interface=options.addr)
    reactor.run()


