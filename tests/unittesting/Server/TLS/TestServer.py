#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import os
import socket
import time
import unittest

from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import load_pem_x509_certificates

from PyNetworkLib.Server.TLS.Server import ThreadingServer
from PyNetworkLib.Server.Utils.DownstreamHandlerBlockByRate import DownstreamHandlerBlockByRate
from PyNetworkLib.TLS.SSLContext import SSLContext

from ..TCP.TestServer import EchoTCPHandler


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(THIS_DIR)))
TEST_CRED_DIR = os.path.join(TESTS_DIR, 'Credentials')
TMP_DIR = os.path.join(TESTS_DIR, 'tmp')


class TestServer(unittest.TestCase):

	def setUp(self):
		if not os.path.exists(TMP_DIR):
			os.makedirs(TMP_DIR)

		# server-side credentials
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

		# client-side credentials
		self._cltPrivKeyPEMPath = os.path.join(TEST_CRED_DIR, 'ed25519', 'leafPrivKey2.pem')
		self._cltCertChainPEMPath = os.path.join(TEST_CRED_DIR, 'ed25519', 'leafCertChain2.pem')
		self._cltSslVrfyCtx = SSLContext.CreateDefaultContext(
			isServerSide=False,
			caPEMorDER=self._caPEMorDER,
			isVerifyRequired=True,
		)
		self._cltSslVrfyCtx.LoadCertChainFiles(
			privKeyPath=self._cltPrivKeyPEMPath,
			certChainPath=self._cltCertChainPEMPath,
			password=b'3ae9de86',
		)
		self._cltSslCtx = SSLContext.CreateDefaultContext(
			isServerSide=False,
			caPEMorDER=self._caPEMorDER,
			isVerifyRequired=False,
		)

	def tearDown(self):
		pass

	def test_Server_TLS_Server_01CreateServer(self):
		# test the creation of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamTCPHdlr=EchoTCPHandler(),
			sslContext=self._sslCtx,
		)
		server.Terminate()

	def test_Server_TLS_Server_02ReqAndResp(self):
		# test using DownstreamHandlerBlockByRate
		dowmHdlr = DownstreamHandlerBlockByRate(
			maxNumRequests=10,
			timeWindowSec=10.0,
			downstreamHandler=EchoTCPHandler(),
			savedStatePath=os.path.join(TMP_DIR, 'testBlockByRateState.json'),
		)

		# test the request and response of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamTCPHdlr=dowmHdlr,
			sslContext=self._sslCtx,
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
				with self._cltSslCtx.WrapSocket(
					sock,
					server_side=False,
					server_hostname='sample1.local'
				) as tsock:
					tsock.connect(serverAddr)
					# send a request to the server
					sentData = b'Hello, World!'
					tsock.sendall(sentData)

					# wait a receive the response
					timeStart = time.time()
					timeOut = 5
					receivedData = b''
					while (time.time() - timeStart < timeOut) and (len(receivedData) < len(sentData)):
						data = tsock.recv(1024)
						if not data:
							break
						receivedData += data

					# check the response
					self.assertEqual(receivedData, sentData)

		finally:
			# terminate the server
			server.Terminate()

	def test_Server_TLS_Server_03ReqAndRespVerifyClient(self):
		# test the request and response of the ThreadingServer class
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamTCPHdlr=EchoTCPHandler(),
			sslContext=self._sslCtxVrfyClt,
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
				with self._cltSslVrfyCtx.WrapSocket(
					sock,
					server_side=False,
					server_hostname='sample1.local'
				) as tsock:
					tsock.connect(serverAddr)
					# send a request to the server
					sentData = b'Hello, World!'
					tsock.sendall(sentData)

					# wait a receive the response
					timeStart = time.time()
					timeOut = 5
					receivedData = b''
					while (time.time() - timeStart < timeOut) and (len(receivedData) < len(sentData)):
						data = tsock.recv(1024)
						if not data:
							break
						receivedData += data

					# check the response
					self.assertEqual(receivedData, sentData)

		finally:
			# terminate the server
			server.Terminate()

