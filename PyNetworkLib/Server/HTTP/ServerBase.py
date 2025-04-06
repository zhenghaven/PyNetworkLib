#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import http.server
import logging
import threading

from .DownstreamHandlerBase import DownstreamHandlerBase
from .Utils.HandlerState import HandlerState


class ServerBase(http.server.HTTPServer):
	'''
	The base class for all HTTP servers in this library.
	'''

	# The downstream HTTP handler to be used by this server.
	downstreamHTTPHdlr: DownstreamHandlerBase

	# The list of commands that are enabled for this server.
	enabledCommands: list[str]

	# The logger to be used by the handlers of this server.  (created and managed by ../BaseServer.BaseServer)
	handlerLogger: logging.Logger

	# The state of the handler.
	handlerState: HandlerState

	# The event set when the server is terminated. (created and managed by ../BaseServer.BaseServer)
	terminateEvent: threading.Event

	# The logger used by this server. (created and managed by ../BaseServer.BaseServer)
	_logger: logging.Logger

	def __init__(
		self,
		server_address,
		RequestHandlerClass,
		downstreamHTTPHdlr: DownstreamHandlerBase,
		enabledCommands: list[str] = ['GET', 'POST'],
		bind_and_activate = True,
	):

		# setting up the downstream handler to be used by this server
		self.downstreamHTTPHdlr = downstreamHTTPHdlr

		# setting up the list of enabled commands
		self.enabledCommands = [
			cmd.upper() for cmd in enabledCommands
		]

		# setting up the state of the handler
		self.handlerState = HandlerState()

		# initializing the server
		super().__init__(
			server_address,
			RequestHandlerClass,
			bind_and_activate,
		)

