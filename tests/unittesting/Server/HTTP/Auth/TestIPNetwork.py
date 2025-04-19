#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import ipaddress
import unittest

import requests

from PyNetworkLib.Server.HTTP.Auth.IPNetwork import IPNetwork
from PyNetworkLib.Server.HTTP.Server import ThreadingServer

from ..TestServer import HappyDownstreamHandler


class TestIPNetwork(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_Server_HTTP_Auth_IPNetwork_01Allowed(self):
		# test the request and response of the ThreadingServer class

		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=IPNetwork(
				ipNetworks=[
					(ipaddress.ip_network('::1/128'), True),
				],
				downstreamHTTPHdlr=HappyDownstreamHandler(),
			),
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			# send a request to the server
			resp = requests.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/',
				timeout=5,
			)
			# check the response
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'OK')
		finally:
			# terminate the server
			server.Terminate()

	def test_Server_HTTP_Auth_IPNetwork_02DeniedByDefault(self):
		# test the request and response of the ThreadingServer class

		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=IPNetwork(
				ipNetworks=[],
				downstreamHTTPHdlr=HappyDownstreamHandler(),
			),
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			# send a request to the server
			resp = requests.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/',
				timeout=5,
			)
			# check the response
			self.assertEqual(resp.status_code, 403)
			self.assertNotEqual(resp.text.find('Forbidden'), -1)
		finally:
			# terminate the server
			server.Terminate()

	def test_Server_HTTP_Auth_IPNetwork_03DeniedBySpec(self):
		# test the request and response of the ThreadingServer class

		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=IPNetwork(
				ipNetworks=[
					(ipaddress.ip_network('::1/128'), False),
				],
				downstreamHTTPHdlr=HappyDownstreamHandler(),
			),
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			# send a request to the server
			resp = requests.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/',
				timeout=5,
			)
			# check the response
			self.assertEqual(resp.status_code, 403)
			self.assertNotEqual(resp.text.find('Forbidden'), -1)
		finally:
			# terminate the server
			server.Terminate()

	def test_Server_HTTP_Auth_IPNetwork_04DeniedByPriority(self):
		# test the request and response of the ThreadingServer class

		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=IPNetwork(
				ipNetworks=[
					(ipaddress.ip_network('::1/128'), False),
					(ipaddress.ip_network('::1/128'), True),
				],
				downstreamHTTPHdlr=HappyDownstreamHandler(),
			),
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			# send a request to the server
			resp = requests.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/',
				timeout=5,
			)
			# check the response
			self.assertEqual(resp.status_code, 403)
			self.assertNotEqual(resp.text.find('Forbidden'), -1)
		finally:
			# terminate the server
			server.Terminate()

	def test_Server_HTTP_Auth_IPNetwork_05AllowedByPriority(self):
		# test the request and response of the ThreadingServer class

		server = ThreadingServer(
			server_address=('127.0.0.1', 0),
			downstreamHTTPHdlr=IPNetwork(
				ipNetworks=[
					(ipaddress.ip_network('127.0.0.1/32'), True),
					(ipaddress.ip_network('127.0.0.1/32'), False),
				],
				downstreamHTTPHdlr=HappyDownstreamHandler(),
			),
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('127.0.0.1', server.GetSrcPort())

			# send a request to the server
			resp = requests.get(
				url=f'http://{serverAddr[0]}:{serverAddr[1]}/',
				timeout=5,
			)
			# check the response
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'OK')
		finally:
			# terminate the server
			server.Terminate()

