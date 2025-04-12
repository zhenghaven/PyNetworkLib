#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import unittest
import urllib.parse

from http import HTTPStatus

import requests

from PyNetworkLib.Server.HTTP.Server import ThreadingServer
from PyNetworkLib.Server.HTTP.HandlerByPath.HandlerByPath import HandlerByPath
from PyNetworkLib.Server.HTTP.HandlerByPath.Utils import (
	HandlerByPathMap,
	EndPointHandler,
)


@EndPointHandler
def HandleEmpty(host, relPath, pyHandler, handlerState, reqState, terminateEvent):
	# set the response code to 200 OK
	pyHandler.SetCodeAndTextMessage(HTTPStatus.OK, f'Empty|{relPath}')

@EndPointHandler
def HandleSlash(host, relPath, pyHandler, handlerState, reqState, terminateEvent):
	# set the response code to 200 OK
	pyHandler.SetCodeAndTextMessage(HTTPStatus.OK, f'Slash|{relPath}')

def HandleHello(host, relPath, pyHandler, handlerState, reqState, terminateEvent):
	# set the response code to 200 OK
	pyHandler.SetCodeAndTextMessage(HTTPStatus.OK, f'Hello|{relPath}')

@EndPointHandler
def HandleHelloEmpty(host, relPath, pyHandler, handlerState, reqState, terminateEvent):
	# set the response code to 200 OK
	pyHandler.SetCodeAndTextMessage(HTTPStatus.OK, f'HelloEmpty|{relPath}')

@EndPointHandler
def HandleHelloWorld(host, relPath, pyHandler, handlerState, reqState, terminateEvent):
	# set the response code to 200 OK
	pyHandler.SetCodeAndTextMessage(HTTPStatus.OK, f'HelloWorld|{relPath}')

@EndPointHandler
def HandleHelloQuery(host, relPath, pyHandler, handlerState, reqState, terminateEvent):
	query = pyHandler.GetRequestQuery()
	try:
		qDict = urllib.parse.parse_qs(query, strict_parsing=True, errors='strict', max_num_fields=10)
		v = qDict['key'][0]
		# set the response code to 200 OK
		pyHandler.SetCodeAndTextMessage(HTTPStatus.OK, f'HelloQuery|{relPath}|{v}')
	except ValueError as e:
		# set the response code to 400 Bad Request
		pyHandler.SetCodeAndTextMessage(HTTPStatus.BAD_REQUEST, f'BadRequest|{relPath}')
		return


WORLD_HANDLER = HandlerByPathMap({
	'': { 'GET': HandleHelloEmpty },
	'/': { 'GET': HandleHello },
	'/World': { 'POST': HandleHelloWorld },
	'/Query': { 'GET': HandleHelloQuery },
})

ROOT_HANDLER = HandlerByPathMap({
	'': { 'GET': HandleEmpty },
	'/': { 'GET': HandleSlash },
	'/Hello': {
		'GET': WORLD_HANDLER,
		'POST': WORLD_HANDLER,
	},
	'/Halo': { 'GET': HandleHello },
})


class TestHandlerByPath(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_Server_HTTP_HandlerByPath_HandlerByPath_01Path(self):
		# test the request and response of the ThreadingServer class

		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=HandlerByPath(handlerFunc=ROOT_HANDLER),
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			session = requests.Session()

			# send get <empty>, but requests will automatically add a /
			resp = session.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}',
				timeout=5,
			)
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'Slash|')

			# send get /
			resp = session.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/',
				timeout=5,
			)
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'Slash|')

			# send get /Hello
			resp = session.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/Hello',
				timeout=5,
			)
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'HelloEmpty|')

			# send get /Hello/
			resp = session.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/Hello/',
				timeout=5,
			)
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'Hello|')

			# send get /Halo/World
			resp = session.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/Halo/World',
				timeout=5,
			)
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'Hello|/World')

			# send post /Hello/World
			resp = session.post(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/Hello/World',
				timeout=5,
			)
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'HelloWorld|')

			# send get /Hello/Query?key=123
			resp = session.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/Hello/Query?key=123',
				timeout=5,
			)
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'HelloQuery||123')


			# some 404 cases


			# send get /Hello/World/
			resp = session.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/Hello/World/',
				timeout=5,
			)
			self.assertEqual(resp.status_code, 404)
			self.assertNotEqual(resp.text.find('Not Found'), -1)

			# send get /Hi
			resp = session.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/Hi',
				timeout=5,
			)
			self.assertEqual(resp.status_code, 404)
			self.assertNotEqual(resp.text.find('Not Found'), -1)

			# # send get /Hello/..
			# resp = session.get(
			# 	url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/Hello/..',
			# 	timeout=5,
			# )
			# self.assertEqual(resp.status_code, 404)
			# self.assertNotEqual(resp.text.find('Not Found'), -1)
		finally:
			# terminate the server
			server.Terminate()

