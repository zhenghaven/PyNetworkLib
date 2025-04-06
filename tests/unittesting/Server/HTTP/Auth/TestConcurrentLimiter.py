#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import threading
import unittest

from http import HTTPStatus

import requests

from PyNetworkLib.Server.HTTP.Auth.ConcurrentLimiter import ConcurrentLimiter
from PyNetworkLib.Server.HTTP.DownstreamHandlerBase import DownstreamHandlerBase
from PyNetworkLib.Server.HTTP.PyHandlerBase import PyHandlerBase
from PyNetworkLib.Server.HTTP.Server import ThreadingServer
from PyNetworkLib.Server.HTTP.Utils.HandlerState import HandlerState
from PyNetworkLib.Server.HTTP.Utils.HostField import HOST_FIELD_TYPES


class BusyHandler(DownstreamHandlerBase):
	'''A busy handler that will block when handling request until the
	server has been terminated.
	'''

	def __init__(
		self,
		startEvent: threading.Event,
		stopEvent: threading.Event,
	) -> None:
		super().__init__()

		self._startEvent = startEvent
		self._stopEvent = stopEvent

	def HandleRequest(
		self,
		host: HOST_FIELD_TYPES,
		relPath: str,
		pyHandler: PyHandlerBase,
		state: HandlerState,
		terminateEvent: threading.Event,
	) -> None:
		'''Handle the request.'''

		self._startEvent.set()

		# block until the server has been terminated
		while not self._stopEvent.is_set():
			self._stopEvent.wait(0.1)

		# set the response code to 200 OK
		pyHandler.SetCodeAndTextMessage(HTTPStatus.OK, 'OK')


class TestConcurrentLimiter(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_Server_HTTP_Auth_ConcurrentLimiter_01Limit(self):
		# test the request and response of the ThreadingServer class
		busyStartEvent = threading.Event()
		busyStopEvent = threading.Event()

		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=ConcurrentLimiter(
				maxConcurrent=1,
				downstreamHTTPHdlr=BusyHandler(
					startEvent=busyStartEvent,
					stopEvent=busyStopEvent,
				),
			),
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			def FirstRequestThread():
				# send a request to the server
				resp = requests.get(
					url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/',
					timeout=5,
				)
				# check the response
				self.assertEqual(resp.status_code, 200)
				self.assertEqual(resp.text, 'OK')


			thread = threading.Thread(
				target=FirstRequestThread,
			)
			thread.start()

			# send another request to the server
			busyStartEvent.wait(5)
			resp = requests.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/',
				timeout=5,
			)

			# check the response
			self.assertEqual(resp.status_code, 403)
			self.assertNotEqual(resp.text.find('Forbidden'), -1)

			# stop the server to stop the busy handler
			busyStopEvent.set()

			# wait for the first request to finish
			thread.join()
		finally:
			# terminate the server
			server.Terminate()

