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

from PyNetworkLib.Server.HTTP.DownstreamHandlerBase import DownstreamHandlerBase
from PyNetworkLib.Server.HTTP.PyHandlerBase import PyHandlerBase
from PyNetworkLib.Server.HTTP.Server import ThreadingServer
from PyNetworkLib.Server.HTTP.Utils.HandlerState import HandlerState
from PyNetworkLib.Server.HTTP.Utils.HostField import HOST_FIELD_TYPES


class HappyDownstreamHandler(DownstreamHandlerBase):
	'''A happy downstream handler that always responds 200 OK.'''

	def HandleRequest(
		self,
		host: HOST_FIELD_TYPES,
		relPath: str,
		pyHandler: PyHandlerBase,
		state: HandlerState,
		terminateEvent: threading.Event,
	) -> None:
		'''Handle the request.'''

		# set the response code to 200 OK
		pyHandler.SetCodeAndTextMessage(HTTPStatus.OK, 'OK')


class TestServer(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_Server_HTTP_Server_01CreateServer(self):
		# test the creation of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=HappyDownstreamHandler(),
		)
		server.Terminate()

	def test_Server_HTTP_Server_02ReqAndResp(self):
		# test the request and response of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=HappyDownstreamHandler(),
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			# send a request to the server
			session = requests.Session()
			resp = session.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/',
				timeout=5,
			)

			# check the response
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'OK')
		finally:
			# terminate the server
			server.Terminate()

	def test_Server_HTTP_Server_03DisabledMethod(self):
		# test the request and response of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=HappyDownstreamHandler(),
			enabledCommands=['POST'],
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			serverAddr = ('::1', server.GetSrcPort())

			# send a request to the server
			session = requests.Session()
			resp = session.post(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/',
				timeout=5,
				data='test',
			)

			# check the response
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'OK')

			# send a request containing a disabled method
			resp = session.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/',
				timeout=5,
			)

			# check the response
			self.assertEqual(resp.status_code, 400)
			self.assertNotEqual(resp.text.find('Bad request'), -1)
		finally:
			# terminate the server
			server.Terminate()

