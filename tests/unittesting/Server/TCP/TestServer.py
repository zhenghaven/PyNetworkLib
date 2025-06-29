#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import socket
import threading
import time
import unittest

from PyNetworkLib.Server.TCP.DownstreamHandlerBase import DownstreamHandlerBase
from PyNetworkLib.Server.TCP.PyHandlerBase import PyHandlerBase
from PyNetworkLib.Server.Utils.HandlerState import HandlerState
from PyNetworkLib.Server.TCP.Server import ThreadingServer


class EchoTCPHandler(DownstreamHandlerBase):
	'''
	A simple TCP handler that echoes back the received data.
	'''

	def HandleRequest(
		self,
		pyHandler: PyHandlerBase,
		handlerState : HandlerState,
		reqState: dict,
		terminateEvent: threading.Event,
	):
		'''Handle the request by echoing back the received data.'''
		# Get the received data from the handler
		data = pyHandler.request.recv(1024)
		pyHandler.request.sendall(data)


class TestServer(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_Server_TCP_Server_01CreateServer(self):
		# test the creation of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamTCPHdlr=EchoTCPHandler(),
		)
		server.Terminate()

	def test_Server_TCP_Server_02ReqAndResp(self):
		# test the request and response of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamTCPHdlr=EchoTCPHandler(),
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
				sock.connect(serverAddr)
				# send a request to the server
				sentData = b'Hello, World!'
				sock.sendall(sentData)

				# wait a receive the response
				timeStart = time.time()
				timeOut = 5
				receivedData = b''
				while (time.time() - timeStart < timeOut) and (len(receivedData) < len(sentData)):
					data = sock.recv(1024)
					if not data:
						break
					receivedData += data

				# check the response
				self.assertEqual(receivedData, sentData)

		finally:
			# terminate the server
			server.Terminate()

