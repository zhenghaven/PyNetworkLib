#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import os
import unittest

import requests

from PyNetworkLib.Client.HTTPS.HTTPSAdapters import HTTPSAdapter
from PyNetworkLib.Server.HTTPS.Auth.TotpToken import TotpToken
from PyNetworkLib.Server.HTTPS.Server import ThreadingServer
from PyNetworkLib.TLS.SSLContext import SSLContext
from PyNetworkLib.Utils.TOTP import Totp
from PyNetworkLib.Utils.TOTPToken import GenTotpToken

from ...HTTP.TestServer import HappyDownstreamHandler


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(THIS_DIR))))
TEST_CRED_DIR = os.path.join(TESTS_DIR, 'Credentials')


class _HappyDownstreamHandler(HappyDownstreamHandler):

	def __init__(self, store) -> None:
		self._store = store

	def HandleRequest(
		self,
		host,
		relPath,
		pyHandler,
		handlerState,
		reqState,
		terminateEvent,
	):
		self._store['current_totp'] = reqState.get('current_totp', None)

		return super().HandleRequest(
			host,
			relPath,
			pyHandler,
			handlerState,
			reqState,
			terminateEvent,
		)


class TestTotpToken(unittest.TestCase):

	def loadCred(self, algo: str) -> None:
		with open(os.path.join(TEST_CRED_DIR, algo, 'rootCaCert.cert'), 'r') as f:
			self._cred[algo].caPEMorDER = f.read()

		# server credentials
		self._cred[algo].svrCertChainPEMPath = os.path.join(TEST_CRED_DIR, algo, 'leafCertChain1.pem')
		self._cred[algo].svrPrivKeyPEMPath = os.path.join(TEST_CRED_DIR, algo, 'leafPrivKey1.pem')

		self._cred[algo].sslCtx = SSLContext.CreateDefaultContext(
			isServerSide=True,
			caPEMorDER=self._cred[algo].caPEMorDER,
			isVerifyRequired=False,
		)
		self._cred[algo].sslCtx.LoadCertChainFiles(
			privKeyPath=self._cred[algo].svrPrivKeyPEMPath,
			certChainPath=self._cred[algo].svrCertChainPEMPath,
			password='3ae9de86',
		)

		# client
		self._cred[algo].httpsAdapter = HTTPSAdapter(caPEMorDER=self._cred[algo].caPEMorDER)

	def setUp(self):
		class _Object:
			pass

		self._totp = Totp(secret=None,secretLen=16)

		self._cred = {
			'ed25519': _Object(),
		}
		self.loadCred('ed25519')

	def tearDown(self):
		pass

	def test_Server_HTTPS_Auth_TotpToken_01ValidToken(self):
		algo = 'ed25519'

		# test the request and response of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=TotpToken(
				totp=self._totp,
				downstreamHTTPHdlr=HappyDownstreamHandler()
			),
			sslContext=self._cred[algo].sslCtx,
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			# send a request to the server
			session = requests.Session()
			session.mount('https://', self._cred[algo].httpsAdapter)
			resp = session.get(
				url=f'https://[{serverAddr[0]}]:{serverAddr[1]}/',
				headers={
					'Host': 'sample1.local',
					'Authorization': f'TOTP_TOKEN {GenTotpToken(self._totp.Now())}'
				},
				verify=True,
				timeout=5,
			)

			# check the response
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'OK')
		finally:
			# terminate the server
			server.Terminate()
		pass

	def test_Server_HTTPS_Auth_TotpToken_02ReqStateHasToken(self):
		algo = 'ed25519'
		reqStateStore = {}

		# test the request and response of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=TotpToken(
				totp=self._totp,
				downstreamHTTPHdlr=_HappyDownstreamHandler(store=reqStateStore)
			),
			sslContext=self._cred[algo].sslCtx,
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			session = requests.Session()

			currTotp = self._totp.Now()

			# send a request to the server
			session.mount('https://', self._cred[algo].httpsAdapter)
			resp = session.get(
				url=f'https://[{serverAddr[0]}]:{serverAddr[1]}/',
				headers={
					'Host': 'sample1.local',
					'Authorization': f'TOTP_TOKEN {GenTotpToken(currTotp)}'
				},
				verify=True,
				timeout=5,
			)

			# check the response
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(resp.text, 'OK')

			# check the request state
			self.assertIn('current_totp', reqStateStore)
			self.assertEqual(reqStateStore['current_totp'], currTotp)
		finally:
			# terminate the server
			server.Terminate()
		pass

	def test_Server_HTTPS_Auth_TotpToken_03InvalidToken(self):
		algo = 'ed25519'

		# test the request and response of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=TotpToken(
				totp=self._totp,
				downstreamHTTPHdlr=HappyDownstreamHandler()
			),
			sslContext=self._cred[algo].sslCtx,
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			session = requests.Session()

			# send a request without Authorization header
			session.mount('https://', self._cred[algo].httpsAdapter)
			resp = session.get(
				url=f'https://[{serverAddr[0]}]:{serverAddr[1]}/',
				headers={
					'Host': 'sample1.local',
				},
				verify=True,
				timeout=5,
			)

			# check the response
			self.assertEqual(resp.status_code, 403)
			self.assertNotEqual(resp.text.find('Forbidden'), -1)

			# send a request with Authorization header in invalid format
			session.mount('https://', self._cred[algo].httpsAdapter)
			resp = session.get(
				url=f'https://[{serverAddr[0]}]:{serverAddr[1]}/',
				headers={
					'Host': 'sample1.local',
					'Authorization': f'TOTP_TOKEN{GenTotpToken(self._totp.Now())}'
				},
				verify=True,
				timeout=5,
			)

			# check the response
			self.assertEqual(resp.status_code, 403)
			self.assertNotEqual(resp.text.find('Forbidden'), -1)

			# send a request with invalid token type
			session.mount('https://', self._cred[algo].httpsAdapter)
			resp = session.get(
				url=f'https://[{serverAddr[0]}]:{serverAddr[1]}/',
				headers={
					'Host': 'sample1.local',
					'Authorization': f'TOTP {GenTotpToken(self._totp.Now())}'
				},
				verify=True,
				timeout=5,
			)

			# check the response
			self.assertEqual(resp.status_code, 403)
			self.assertNotEqual(resp.text.find('Forbidden'), -1)

			# send a request with invalid token format
			invalidToken = GenTotpToken(self._totp.Now()).replace(':', '_')
			session.mount('https://', self._cred[algo].httpsAdapter)
			resp = session.get(
				url=f'https://[{serverAddr[0]}]:{serverAddr[1]}/',
				headers={
					'Host': 'sample1.local',
					'Authorization': f'TOTP_TOKEN {invalidToken}'
				},
				verify=True,
				timeout=5,
			)

			# check the response
			self.assertEqual(resp.status_code, 403)
			self.assertNotEqual(resp.text.find('Forbidden'), -1)

			# send a request with invalid salt length
			invalidToken = GenTotpToken(self._totp.Now())[56:]
			session.mount('https://', self._cred[algo].httpsAdapter)
			resp = session.get(
				url=f'https://[{serverAddr[0]}]:{serverAddr[1]}/',
				headers={
					'Host': 'sample1.local',
					'Authorization': f'TOTP_TOKEN {invalidToken}'
				},
				verify=True,
				timeout=5,
			)

			# check the response
			self.assertEqual(resp.status_code, 403)
			self.assertNotEqual(resp.text.find('Forbidden'), -1)

			# send a request with invalid token hash
			invalidToken = GenTotpToken(self._totp.Now())[1:]
			session.mount('https://', self._cred[algo].httpsAdapter)
			resp = session.get(
				url=f'https://[{serverAddr[0]}]:{serverAddr[1]}/',
				headers={
					'Host': 'sample1.local',
					'Authorization': f'TOTP_TOKEN {invalidToken}'
				},
				verify=True,
				timeout=5,
			)

			# check the response
			self.assertEqual(resp.status_code, 403)
			self.assertNotEqual(resp.text.find('Forbidden'), -1)
		finally:
			# terminate the server
			server.Terminate()

