#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import os
import threading
import unittest

from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509 import Certificate, load_pem_x509_certificates
from http import HTTPStatus

import requests

from PyNetworkLib.Client.HTTPS.HTTPSAdapters import HTTPSAdapter
from PyNetworkLib.Server.HTTPS.Auth.TLS import TLS as TLSAuth
from PyNetworkLib.Server.HTTPS.Server import ThreadingServer
from PyNetworkLib.Server.HTTP.DownstreamHandlerBase import DownstreamHandlerBase
from PyNetworkLib.Server.HTTP.PyHandlerBase import PyHandlerBase
from PyNetworkLib.Server.HTTP.Utils.HandlerState import HandlerState
from PyNetworkLib.Server.HTTP.Utils.HostField import HOST_FIELD_TYPES
from PyNetworkLib.TLS.SSLContext import SSLContext


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(THIS_DIR))))
TEST_CRED_DIR = os.path.join(TESTS_DIR, 'Credentials')


class CertCheckHandler(DownstreamHandlerBase):
	'''A handler that will store the certificate check result'''

	def __init__(
		self,
		store: dict,
	) -> None:
		super().__init__()

		self._store = store

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

		self._store['peer_cert'] = reqState.get('peer_cert', None)
		self._store['peer_intermediate_cert'] = reqState.get('peer_intermediate_cert', None)
		self._store['peer_root_cert'] = reqState.get('peer_root_cert', None)
		self._store['peer_common_name'] = reqState.get('peer_common_name', None)
		self._store['peer_alt_name'] = reqState.get('peer_alt_name', None)

		# set the response code to 200 OK
		pyHandler.SetCodeAndTextMessage(HTTPStatus.OK, 'OK')


class TestTls(unittest.TestCase):

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

		self._cred[algo].sslCtxVrfyClt = SSLContext.CreateDefaultContext(
			isServerSide=True,
			caPEMorDER=self._cred[algo].caPEMorDER,
			isVerifyRequired=True,
		)
		self._cred[algo].sslCtxVrfyClt.LoadCertChainFiles(
			privKeyPath=self._cred[algo].svrPrivKeyPEMPath,
			certChainPath=self._cred[algo].svrCertChainPEMPath,
			password='3ae9de86',
		)

		# client credentials
		self._cred[algo].cltPrivKeyPEMPath = os.path.join(TEST_CRED_DIR, algo, 'leafPrivKey2.pem')
		self._cred[algo].cltCertChainPEMPath = os.path.join(TEST_CRED_DIR, algo, 'leafCertChain2.pem')
		with open(self._cred[algo].cltCertChainPEMPath, 'r') as f:
			self._cred[algo].cltCertChainPEM = f.read()
		self._cred[algo].cltCertChain = load_pem_x509_certificates(self._cred[algo].cltCertChainPEM.encode())

		self._cred[algo].httpsAdapter = HTTPSAdapter(caPEMorDER=self._cred[algo].caPEMorDER)

		self._cred[algo].httpsAdapterVrfyClt = HTTPSAdapter(caPEMorDER=self._cred[algo].caPEMorDER)
		self._cred[algo].httpsAdapterVrfyClt.LoadClientKeyAndCertFiles(
			privKeyPath=self._cred[algo].cltPrivKeyPEMPath,
			certChainPath=self._cred[algo].cltCertChainPEMPath,
			password='3ae9de86',
		)

	def setUp(self):
		class _Object:
			pass

		self._cred = {
			'ed25519': _Object(),
			'ecdsa': _Object(),
			'rsa': _Object(),
		}
		self.loadCred('ed25519')
		self.loadCred('ecdsa')
		self.loadCred('rsa')

	def tearDown(self):
		pass

	def TestClientHasCert(self, algo):
		# test the request and response of the ThreadingServer class
		peerCredStore = {}
		server = ThreadingServer(
			server_address=('::1', 0),
			downstreamHTTPHdlr=TLSAuth(
				rootCaCertPEM=self._cred[algo].caPEMorDER,
				downstreamHTTPHdlr=CertCheckHandler(store=peerCredStore)
			),
			sslContext=self._cred[algo].sslCtxVrfyClt,
		)

		try:
			# start the server
			server.ThreadedServeUntilTerminate()

			# get the server address
			serverAddr = ('::1', server.GetSrcPort())

			# send a request to the server
			session = requests.Session()
			session.mount('https://', self._cred[algo].httpsAdapterVrfyClt)
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

			# check the peer certificate chain
			self.assertIn('peer_root_cert', peerCredStore)
			self.assertIsInstance(peerCredStore['peer_root_cert'], Certificate)
			self.assertEqual(
				peerCredStore['peer_root_cert'].public_bytes(Encoding.PEM).decode(),
				self._cred[algo].caPEMorDER
			)

			self.assertIn('peer_intermediate_cert', peerCredStore)
			self.assertEqual(len(peerCredStore['peer_intermediate_cert']), 1)
			self.assertEqual(
				peerCredStore['peer_intermediate_cert'][0].public_bytes(Encoding.PEM).decode(),
				self._cred[algo].cltCertChain[1].public_bytes(Encoding.PEM).decode()
			)

			self.assertIn('peer_cert', peerCredStore)
			self.assertIsInstance(peerCredStore['peer_cert'], Certificate)
			self.assertEqual(
				peerCredStore['peer_cert'].public_bytes(Encoding.PEM).decode(),
				self._cred[algo].cltCertChain[0].public_bytes(Encoding.PEM).decode()
			)

			self.assertIn('peer_common_name', peerCredStore)
			self.assertEqual(peerCredStore['peer_common_name'], 'sample2.local')

			self.assertIn('peer_alt_name', peerCredStore)
			self.assertEqual(
				sorted(peerCredStore['peer_alt_name']),
				sorted(['sample2.local', 'test2.local'])
			)

		finally:
			# terminate the server
			server.Terminate()

	def test_Server_HTTPS_Auth_TLS_01ClientHasCert(self):
		self.TestClientHasCert('ed25519')
		self.TestClientHasCert('ecdsa')
		self.TestClientHasCert('rsa')

