
#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import socketserver

from ...TLS.SSLContext import SSLContext
from ..HTTP.DownstreamHandlerBase import DownstreamHandlerBase
from ..HTTP.Server import PyServer as HTTPPyServer
from ..PySocketServer import FromPySocketServer
from ..TLS.ListenSocket import ListenSocket as TLSListenSocket


class PyServer(HTTPPyServer):

	allow_reuse_address = 0 # This is set to 0 to prevent the server from reusing the address.

	def __init__(
		self,
		server_address,
		downstreamHTTPHdlr: DownstreamHandlerBase,
		sslContext: SSLContext,
		enabledCommands: list[str] = ['GET', 'POST'],
		bind_and_activate = True,
	):
		super().__init__(
			server_address=server_address,
			downstreamHTTPHdlr=downstreamHTTPHdlr,
			enabledCommands=enabledCommands,
			bind_and_activate=bind_and_activate,
		)

		self._sslCtx = sslContext
		self.socket = TLSListenSocket(
			sock=self.socket,
			sslContext=self._sslCtx,
		)


class PyThreadingServer(socketserver.ThreadingMixIn, PyServer):
	daemon_threads = True


@FromPySocketServer
class Server(PyServer):
	pass


@FromPySocketServer
class ThreadingServer(PyThreadingServer):
	pass
