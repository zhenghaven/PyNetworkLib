#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import logging
import time
import unittest
import socket
import socketserver

from PyNetworkLib.Server.PySocketServer import FromPySocketServer
from PyNetworkLib.Server.ServerBase import ServerBase


_LOGGER = logging.getLogger(__name__)


class EchoingTCPHandler(socketserver.StreamRequestHandler):

	def handle(self):
		_LOGGER.info('Received data from %s', self.client_address)
		data = self.rfile.readline()
		_LOGGER.info('Received data: %s', data)
		self.wfile.write(data)


class BusyTCPHandler(socketserver.StreamRequestHandler):

	def handle(self):
		self.server: ServerBase
		while not self.server.terminateEvent.is_set():
			self.server.busyLoopCount += 1


class TestPySocketServer(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_Server_PySocketServer_01CreateClass(self):
		# test the creation of the PySocketServer class
		@FromPySocketServer
		class TestServer(socketserver.TCPServer):
			pass

		self.assertTrue(issubclass(TestServer, socketserver.TCPServer))
		self.assertTrue(issubclass(TestServer, ServerBase))

	def test_Server_PySocketServer_02CreateInstance(self):
		# test the creation of the PySocketServer instance
		@FromPySocketServer
		class TestServer(socketserver.TCPServer):
			pass

		server = TestServer(
			server_address=('127.0.0.1', 0),
			RequestHandlerClass=socketserver.BaseRequestHandler,
			serverInit = {},
		)
		# server.ServerInit()
		try:
			self.assertIsInstance(server, socketserver.TCPServer)
			self.assertIsInstance(server, ServerBase)
		finally:
			server.Terminate()

	def test_Server_PySocketServer_03ThreadedServeUntilTerminate(self):
		# test the echo server
		@FromPySocketServer
		class TestServer(socketserver.TCPServer):
			pass

		server = TestServer(
			server_address=('127.0.0.1', 0),
			RequestHandlerClass=socketserver.BaseRequestHandler,
			serverInit = {},
		)
		server.ThreadedServeUntilTerminate()
		serverPort = server.GetSrcPort()

		try:
			testData = b'Hello, world\n'
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
				client.connect(('127.0.0.1', serverPort))
				client.sendall(testData)
				# client.settimeout(0.5)
				# echoData = client.recv(1024)
		finally:
			server.Terminate()

	def test_Server_PySocketServer_04EchoServer(self):
		# test the echo server
		@FromPySocketServer
		class TestServer(socketserver.TCPServer):
			pass

		server = TestServer(
			server_address=('127.0.0.1', 0),
			RequestHandlerClass=EchoingTCPHandler,
			serverInit = {},
		)
		server.ThreadedServeUntilTerminate()
		serverPort = server.GetSrcPort()

		try:
			testData = b'Hello, world\n'
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
				client.connect(('127.0.0.1', serverPort))
				client.sendall(testData)
				echoData = ''
				while not (echoData.find('\n') != -1):
					echoData += client.recv(1024).decode('utf-8')

			self.assertEqual(echoData, testData.decode('utf-8'))
		finally:
			server.Terminate()

	def test_Server_PySocketServer_05BusyServer(self):
		# test the echo server
		@FromPySocketServer
		class TestServer(socketserver.TCPServer):
			pass

		server = TestServer(
			server_address=('127.0.0.1', 0),
			RequestHandlerClass=BusyTCPHandler,
			serverInit = {
				"addData": {
					'busyLoopCount': 0,
				},
			},
		)
		server.ThreadedServeUntilTerminate()
		serverPort = server.GetSrcPort()

		try:
			testData = b'Hello, world\n'
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
				client.connect(('127.0.0.1', serverPort))

				# send the test data to trigger the busy loop
				client.sendall(testData)

				# wait for the server to start the busy loop and iterate a few times
				while server.busyLoopCount < 10:
					time.sleep(0.1)

				# now that the busy loop counter should be greater or equal to 10
				self.assertGreaterEqual(server.busyLoopCount, 10)
		finally:
			server.Terminate()

