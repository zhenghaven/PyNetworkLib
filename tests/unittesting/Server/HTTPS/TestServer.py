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

from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import load_pem_x509_certificates

from PyNetworkLib.Client.HTTPS.HTTPSAdapters import HTTPSAdapter
from PyNetworkLib.Server.HTTPS.Server import ThreadingServer
from PyNetworkLib.Server.Utils.DownstreamHandlerBlockByRate import DownstreamHandlerBlockByRate
from PyNetworkLib.TLS.SSLContext import SSLContext

from ..HTTP.TestServer import HappyDownstreamHandler


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(THIS_DIR)))
TEST_CRED_DIR = os.path.join(TESTS_DIR, 'Credentials')
TMP_DIR = os.path.join(TESTS_DIR, 'tmp')


class TestServer(unittest.TestCase):

	def setUp(self):
		if not os.path.exists(TMP_DIR):
			os.makedirs(TMP_DIR)

		with open(os.path.join(TEST_CRED_DIR, 'ed25519', 'rootCaCert.cert'), 'r') as f:
			self._caPEMorDER = f.read()

		self._svrCertChainPEMPath = os.path.join(TEST_CRED_DIR, 'ed25519', 'leafCertChain1.pem')
		with open(self._svrCertChainPEMPath, 'r') as f:
			self._svrCertChainPEM = f.read()
		self._svrCertChain = load_pem_x509_certificates(self._svrCertChainPEM.encode())

		self._svrPrivKeyPEMPath = os.path.join(TEST_CRED_DIR, 'ed25519', 'leafPrivKey1.pem')
		with open(self._svrPrivKeyPEMPath, 'r') as f:
			self._svrPrivKeyPEM = f.read()
		self._svrPrivKey = load_pem_private_key(
			self._svrPrivKeyPEM.encode(),
			password=b'3ae9de86',
		)

		self._cltPrivKeyPEMPath = os.path.join(TEST_CRED_DIR, 'ed25519', 'leafPrivKey2.pem')
		self._cltCertChainPEMPath = os.path.join(TEST_CRED_DIR, 'ed25519', 'leafCertChain2.pem')

		self._sslCtx = SSLContext.CreateDefaultContext(
			isServerSide=True,
			caPEMorDER=self._caPEMorDER,
			isVerifyRequired=False,
		)
		self._sslCtx.LoadCertChain(
			privKey=self._svrPrivKey,
			certChain=self._svrCertChain,
			tmpDir=TMP_DIR,
		)

		self._sslCtxVrfyClt = SSLContext.CreateDefaultContext(
			isServerSide=True,
			caPEMorDER=self._caPEMorDER,
			isVerifyRequired=True,
		)
		self._sslCtxVrfyClt.LoadCertChain(
			privKey=self._svrPrivKey,
			certChain=self._svrCertChain,
			tmpDir=TMP_DIR,
		)

		self._httpsAdapter = HTTPSAdapter(caPEMorDER=self._caPEMorDER)

		self._httpsAdapterVrfyClt = HTTPSAdapter(caPEMorDER=self._caPEMorDER)
		self._httpsAdapterVrfyClt.LoadClientKeyAndCertFiles(
			privKeyPath=self._cltPrivKeyPEMPath,
			certChainPath=self._cltCertChainPEMPath,
			password='3ae9de86',
		)

	def tearDown(self):
		pass

	def test_Server_HTTPS_Server_01CreateServer(self):
		# test the creation of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=HappyDownstreamHandler(),
			sslContext=self._sslCtx,
		)
		server.Terminate()

	def test_Server_HTTPS_Server_02ReqAndResp(self):
		# test using DownstreamHandlerBlockByRate
		dowmHdlr = DownstreamHandlerBlockByRate(
			maxNumRequests=10,
			timeWindowSec=10.0,
			downstreamHandler=HappyDownstreamHandler(),
			savedStatePath=os.path.join(TMP_DIR, 'testBlockByRateState.json'),
		)

		# test the request and response of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=dowmHdlr,
			sslContext=self._sslCtx,
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			# send a request to the server
			session = requests.Session()
			session.mount('https://', self._httpsAdapter)
			resp = session.get(
				url=f'https://[{serverAddr[0]}]:{serverAddr[1]}/',
				headers={
					'Host': 'sample1.local',
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

	def test_Server_HTTPS_Server_03MutualAuth(self):
		# test the request and response of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=HappyDownstreamHandler(),
			sslContext=self._sslCtxVrfyClt,
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			# send a request to the server
			session = requests.Session()
			session.mount('https://', self._httpsAdapterVrfyClt)
			resp = session.get(
				url=f'https://[{serverAddr[0]}]:{serverAddr[1]}/',
				headers={
					'Host': 'sample1.local',
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

