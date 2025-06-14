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
from PyNetworkLib.Server.HTTP.Utils.HostField import HOST_FIELD_TYPES
from PyNetworkLib.Server.Utils.HandlerState import HandlerState


class HappyDownstreamHandler(DownstreamHandlerBase):
	'''A happy downstream handler that always responds 200 OK.'''

	def HandleRequest(
		self,
		host: HOST_FIELD_TYPES,
		relPath: str,
		pyHandler: PyHandlerBase,
		handlerState: HandlerState,
		reqState: dict,
		terminateEvent: threading.Event,
	) -> None:
		'''Handle the request.'''

		# set the response code to 200 OK
		pyHandler.SetCodeAndTextMessage(HTTPStatus.OK, 'OK')


class JSONDownstreamHandler(DownstreamHandlerBase):
	'''A downstream handler that expects a JSON request body and
	responds with a JSON response.
	'''

	def HandleRequest(
		self,
		host: HOST_FIELD_TYPES,
		relPath: str,
		pyHandler: PyHandlerBase,
		handlerState: HandlerState,
		reqState: dict,
		terminateEvent: threading.Event,
	) -> None:
		'''Handle the request.'''
		try:
			# get the request body
			body = pyHandler.GetRequestJSON()
		except Exception as e:
			pyHandler.log_error(
				'Failed to parse JSON request body: %s',
				str(e),
			)
			# set the response code to 400 Bad Request
			pyHandler.SetCodeAndTextMessage(HTTPStatus.BAD_REQUEST, 'Bad Request')
		else:
			# echo the request body back to the client with a 200 OK response
			pyHandler.SetJSONBodyFromDict(body, indent='\t', statusCode=HTTPStatus.OK)


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

	def test_Server_HTTP_Server_04JSON(self):
		# test the request and response of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=JSONDownstreamHandler(),
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			reqBody = {
				'key1': 'value1',
				'key2': 'value2',
			}

			# send a request to the server
			session = requests.Session()
			resp = session.post(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/',
				json=reqBody,
				timeout=5,
			)

			# check the response
			self.assertEqual(resp.status_code, 200)
			respBody = resp.json()
			self.assertEqual(respBody, reqBody)
		finally:
			# terminate the server
			server.Terminate()

