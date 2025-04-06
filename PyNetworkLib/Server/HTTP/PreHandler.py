#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import http.server
import http
import logging

from .PyHandlerBase import PyHandlerBase
from .ServerBase import ServerBase
from .Utils.HostField import ParseHostField


class PreHandler(PyHandlerBase):

	# The server object that manages this handler.
	server: ServerBase

	def handle_one_request(self):
		'''Handle a single HTTP request.

		The parent class (BaseHTTPRequestHandler) has this method implemented,
		but we need authentication to be done up front, and we need a slightly
		different way to pass the request to the downstream handler.
		So most of the code in this function is copied from the parent class,
		with minor modifications.
		'''

		try:
			self.raw_requestline = self.rfile.readline(65537)
			if len(self.raw_requestline) > 65536:
				self.requestline = ''
				self.request_version = ''
				self.command = ''
				self.send_error(http.HTTPStatus.REQUEST_URI_TOO_LONG)
				return
			if not self.raw_requestline:
				self.close_connection = True
				return
			if not self.parse_request():
				# An error code has been sent, just exit
				return

			# MODIFICATION: The following part is modified
			'''
			mname = 'do_' + self.command
			if not hasattr(self, mname):
				self.send_error(
					http.HTTPStatus.NOT_IMPLEMENTED,
					"Unsupported method (%r)" % self.command)
				return
			method = getattr(self, mname)
			method()
			'''
			# MODIFICATION: instead of looking for the method and then calling it
			# we just call HandleOneRequest directly.
			self.HandleOneRequest()

			# MODIFICATION: The rest remains the same
			self.wfile.flush() #actually send the response if not already done.
		except TimeoutError as e:
			#a read or a write timed out.  Discard this connection
			self.log_error("Request timed out: %r", e)
			self.close_connection = True
			return

	def log_message(self, format, *args):
		return self.LogMessageWithLevel(
			logging.INFO,
			format,
			*args,
		)

	def log_error(self, format, *args):
		return self.LogMessageWithLevel(
			logging.ERROR,
			format,
			*args,
		)

	# our own methods start from here

	def LogMessageWithLevel(self, level: int, format: str, *args):
		'''Log a message with the given level.

		The parent class (BaseHTTPRequestHandler) has `log_message` implemented,
		but it's not using the logging module, and instead it writes to stderr.
		So the log message is not being handled uniformly by the logging module.
		'''

		self.server.handlerLogger.log(
			level,
			f'[{self.client_address}]->[{self.address_string()}] ' + format,
			*args,
		)

	def LogDebug(self, format: str, *args):
		'''Log a debug message.'''
		self.LogMessageWithLevel(
			logging.DEBUG,
			format,
			*args,
		)

	def HandleOneRequest(self):
		'''Handle a single HTTP request.

		This is the main method that handles the request. It is called by
		handle_one_request() after the request has been parsed.
		'''

		self.server.handlerLogger.debug(
			'Received %s request for %s',
			self.command,
			self.path,
		)

		# check if the command is enabled
		if self.command not in self.server.enabledCommands:
			self.send_error(http.HTTPStatus.BAD_REQUEST, 'Bad request')
			return

		# Get host name from the request header
		host = self.headers.get('Host', None)
		if host is None:
			self.send_error(http.HTTPStatus.BAD_REQUEST, 'Bad request')
			return
		host = ParseHostField(
			host=host,
			defaultPort=self.server.server_address[1]
		)

		self.server.handlerLogger.debug(
			'Pass %s request to %s for %s to downstream handler',
			self.command,
			host,
			self.path,
		)

		try:
			# let the downstream handler handle the request
			self.server.downstreamHTTPHdlr.HandleRequest(
				host=host,
				relPath=self.path,
				pyHandler=self,
				state=self.server.handlerState,
				terminateEvent=self.server.terminateEvent,
			)
		except Exception as e:
			self.server.handlerLogger.error(
				'Exception in downstream handler: %s',
				e,
			)
			self.SetCodeAndTextMessage(
				http.HTTPStatus.INTERNAL_SERVER_ERROR,
				'Internal server error',
			)

		# send the response
		if (
			# ensure that the server is not terminated
			(not self.server.terminateEvent.is_set())
			# and the response has not been sent yet
			and (not self.hasResponseSent)
		):
			self.DoResponse()

