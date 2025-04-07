#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import os
import ssl

from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.x509.base import Certificate
from requests.adapters import HTTPAdapter

from ...TLS.SSLContext import SSLContext


class HTTPSAdapter(HTTPAdapter):

	def __init__(
		self,
		*args,
		caPEMorDER: str | bytes,
		verify: bool = True,
		**kwargs,
	) -> None:
		super().__init__(
			*args,
			**kwargs,
		)

		self._sslCtx = SSLContext.CreateDefaultContext(
			isServerSide=False, # this adapter is for client side
			caPEMorDER=caPEMorDER,
			isVerifyRequired=verify,
		)

		if not verify:
			# for the client side, if verify is not required,
			# we need to set the verify mode to CERT_NONE
			self._sslCtx.SetVerifyModeCertNone()

	def LoadClientKeyAndCertFiles(
		self,
		privKeyPath: os.PathLike,
		certChainPath: os.PathLike,
		password: str | bytes | None=None,
	) -> None:
		self._sslCtx.LoadCertChainFiles(
			privKeyPath=privKeyPath,
			certChainPath=certChainPath,
			password=password,
		)

	def LoadClientKeyAndCert(
		self,
		privKey: PrivateKeyTypes,
		certChain: list[Certificate],
		tmpDir: os.PathLike,
	) -> None:
		self._sslCtx.LoadCertChain(
			privKey=privKey,
			certChain=certChain,
			tmpDir=tmpDir,
		)

	def EnableTlsV1_2(self) -> None:
		self._sslCtx.EnableTlsV1_2()

	def build_connection_pool_key_attributes(self, request, verify, cert=None):
		host_params, pool_kwargs = super().build_connection_pool_key_attributes(
			request,
			verify=verify,
			cert=None,
		)

		for key, header in request.headers.items():
			if key.lower() == 'host':
				pool_kwargs['server_hostname'] = header

		pool_kwargs['ssl_minimum_version'] = ssl.TLSVersion.TLSv1_3

		# use our own SSL context
		pool_kwargs['ssl_context'] = self._sslCtx._pySslCtx

		return (host_params, pool_kwargs)

