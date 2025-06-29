#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import socketserver
import logging
import threading

from ..Utils.HandlerState import HandlerState
from .DownstreamHandlerBase import DownstreamHandlerBase


class ServerBase(socketserver.TCPServer):
	'''
	The base class for all TCP servers in this library.
	'''

	# The downstream TCP handler to be used by this server.
	downstreamTCPHdlr: DownstreamHandlerBase

	# The state of the handler.
	handlerState: HandlerState

	# The logger to be used by the handlers of this server.  (created and managed by ../BaseServer.BaseServer)
	handlerLogger: logging.Logger

	# The event set when the server is terminated. (created and managed by ../BaseServer.BaseServer)
	terminateEvent: threading.Event

	# The logger used by this server. (created and managed by ../BaseServer.BaseServer)
	_logger: logging.Logger

	def __init__(
		self,
		server_address,
		RequestHandlerClass,
		downstreamTCPHdlr: DownstreamHandlerBase,
		bind_and_activate = True,
	):

		# setting up the downstream handler to be used by this server
		self.downstreamTCPHdlr = downstreamTCPHdlr

		# setting up the state of the handler
		self.handlerState = HandlerState()

		# initializing the server
		super().__init__(
			server_address,
			RequestHandlerClass,
			bind_and_activate,
		)

