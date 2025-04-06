#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import unittest

import requests

from PyNetworkLib.Server.HTTP.Auth.RateLimiter import RateLimiter
from PyNetworkLib.Server.HTTP.DownstreamHandlerBase import DownstreamHandlerBase
from PyNetworkLib.Server.HTTP.PyHandlerBase import PyHandlerBase
from PyNetworkLib.Server.HTTP.Server import ThreadingServer
from PyNetworkLib.Server.HTTP.Utils.HandlerState import HandlerState
from PyNetworkLib.Server.HTTP.Utils.HostField import HOST_FIELD_TYPES

from ..TestServer import HappyDownstreamHandler


class TestRateLimiter(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_Server_HTTP_Auth_RateLimiter_01Limit(self):
		# test the request and response of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=RateLimiter(
				maxReq=1,
				timePeriodSec=600, # it only takes 1 request every 10 minutes
				downstreamHTTPHdlr=HappyDownstreamHandler(),
			),
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			# the first request should be handled by the HappyDownstreamHandler
			resp = requests.get(
				url=f'http://[{serverAddr[0]}]:{serverAddr[1]}/',
				timeout=5,
			)
			# check the response
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'OK')

			# The second request should be blocked by the RateLimiter
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

