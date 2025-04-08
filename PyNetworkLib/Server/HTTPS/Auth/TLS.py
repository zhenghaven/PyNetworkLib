#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import datetime
# import logging
import ssl
import threading

from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey, ECDSA
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.x509 import (
	load_pem_x509_certificates,
	load_der_x509_certificate,
	Certificate,
	DNSName as x509DNSName,
	NameOID as x509NameOID,
	SubjectAlternativeName as x509SubjectAlternativeName,
)
from cryptography.hazmat.primitives.serialization import (
	Encoding,
	PublicFormat,
)

from ...HTTP.DownstreamHandlerBase import DownstreamHandlerBase
from ...HTTP.PreHandler import PreHandler
from ...HTTP.Utils.HandlerState import HandlerState
from ...HTTP.Utils.HostField import HOST_FIELD_TYPES


class TLS(DownstreamHandlerBase):
	'''A concurrent limiter that limits the number of concurrent requests
	being handled.
	'''

	def __init__(
		self,
		rootCaCertPEM: str | bytes,
		downstreamHTTPHdlr: DownstreamHandlerBase,
	) -> None:
		'''
		Constructor for the RateLimiter class.
		'''

		super().__init__()

		if isinstance(rootCaCertPEM, str):
			rootCaCertPEM = rootCaCertPEM.encode()
		self._rootCaCerts = load_pem_x509_certificates(rootCaCertPEM)
		# self._caStore = x509Store(self._rootCaCerts)
		# self._policyBuilder = x509PolicyBuilder().store(self._caStore)
		# self._verifier = self._policyBuilder.build_client_verifier()

		self._downstreamHTTPHdlr = downstreamHTTPHdlr

	@classmethod
	def _PubKeyToRawBytes(
		cls,
		pubKey: PublicKeyTypes,
	) -> bytes:
		'''Convert the public key to raw bytes.'''
		return pubKey.public_bytes(
			encoding = Encoding.DER,
			format   = PublicFormat.SubjectPublicKeyInfo,
		)

	@classmethod
	def _FindRootCaCert(
		cls,
		certChain: list[Certificate],
		trustedCerts: list[Certificate],
	) -> Certificate | None:
		'''Find the root CA certificate from the trusted store and return it.'''

		def _IsCaCert(
			certChain: list[Certificate],
			trustedCert: Certificate,
		) -> bool:
			'''Check if the trusted certificate is the CA certificate of the given chain.'''
			# search from the end of the chain
			for cert in reversed(certChain):
				if cls._PubKeyToRawBytes(cert.public_key()) == cls._PubKeyToRawBytes(trustedCert.public_key()):
				# if cert.subject == trustedCert.subject:
					# found the CA certificate in the chain
					return True
				if cert.issuer == trustedCert.subject:
					# this cert is issued by the trusted cert
					return True

			# the trusted cert is not the CA of the given chain
			return False

		for trustedCert in trustedCerts:
			if _IsCaCert(certChain, trustedCert):
				# found the CA certificate in the chain
				return trustedCert

		# cannot find the CA certificate for the given chain
		return None

	@classmethod
	def _VerifyCertSignature(
		cls,
		pubKey: PublicKeyTypes,
		subjCert: Certificate,
	) -> bool:
		'''Verify the certificate signature.'''

		if isinstance(pubKey, Ed25519PublicKey):
			pubKey.verify(
				signature=subjCert.signature,
				data=subjCert.tbs_certificate_bytes,
			)
		elif isinstance(pubKey, EllipticCurvePublicKey):
			pubKey.verify(
				signature=subjCert.signature,
				data=subjCert.tbs_certificate_bytes,
				signature_algorithm=ECDSA(
					algorithm=subjCert.signature_hash_algorithm,
				),
			)
		elif isinstance(pubKey, RSAPublicKey):
			pubKey.verify(
				signature=subjCert.signature,
				data=subjCert.tbs_certificate_bytes,
				padding=subjCert.signature_algorithm_parameters,
				algorithm=subjCert.signature_hash_algorithm,
			)

	@classmethod
	def _VerifyCertificate(
		cls,
		subjCert: Certificate,
		issuerCert: Certificate,
	) -> tuple[bool, str]:
		'''Verify the certificate.'''

		try:
			cls._VerifyCertSignature(
				pubKey=issuerCert.public_key(),
				subjCert=subjCert,
			)
		except Exception as e:
			# the certificate is not valid
			return False, f'Failed to verify the certificate signature: {e}'

		now = datetime.datetime.now(datetime.timezone.utc)
		if (
			now < subjCert.not_valid_before_utc
			or now > subjCert.not_valid_after_utc
		):
			# the certificate is not in the valid time range
			return False, 'The certificate is not in the valid time range.'

		return True, None

	@classmethod
	def _GetCertOfNextLevel(
		cls,
		certChain: list[Certificate],
		trustedCert: Certificate,
	) -> tuple[
		list[Certificate], # the remaining cert chain
		Certificate | None, # the next level cert found in the chain
		str | None, # the error message
	]:
		remainingCertChain: list[Certificate] = certChain.copy()

		# search from the end of the chain
		for revI in reversed(range(len(remainingCertChain))):
			cert = remainingCertChain[revI]
			# case 1: trusted cert is in the chain
			if cls._PubKeyToRawBytes(cert.public_key()) == cls._PubKeyToRawBytes(trustedCert.public_key()):
			# if cert.subject == trustedCert.subject:
				# found the trusted cert in the chain
				# remove the trusted cert from the chain
				remainingCertChain.pop(revI)
				# print('remove redundant cert from the chain')
				return remainingCertChain, None, None

			# case 2: trusted cert is the issuer of the current cert
			if cert.issuer == trustedCert.subject:
				# this cert is issued by the trusted cert
				# check its signature
				res, errMsg = cls._VerifyCertificate(
					subjCert=cert,
					issuerCert=trustedCert,
				)
				# print(errMsg)
				if res:
					# the signature is valid
					# remove the trusted cert from the chain
					remainingCertChain.pop(revI)
					return remainingCertChain, cert, None

		return remainingCertChain, None, 'Cannot find the cert of next level.'

	@classmethod
	def _VerifyCertChain(
		cls,
		certChain: list[Certificate],
		trustedCert: Certificate,
	) -> tuple[list[Certificate], str | None]:
		'''Verify the certificate chain, and return the verified chain in order.'''

		verifiedChain: list[Certificate] = []

		while len(certChain) > 0:
			certChain, nextCert, errMsg = cls._GetCertOfNextLevel(
				certChain=certChain,
				trustedCert=trustedCert,
			)
			if errMsg is not None:
				# there is an error in the chain
				return [], errMsg
			if nextCert is None:
				# removed redundant cert from the chain
				pass
			else:
				# add the next cert to the verified chain
				# the child cert is always added to the front of the chain
				# so that the leaf cert will be the first one in the chain
				verifiedChain.insert(0, nextCert)
				# set the next cert as the trusted cert
				trustedCert = nextCert

		return verifiedChain, None

	def HandleRequest(
		self,
		host: HOST_FIELD_TYPES,
		relPath: str,
		pyHandler: PreHandler,
		handlerState: HandlerState,
		reqState: dict,
		terminateEvent: threading.Event,
	) -> None:
		'''Handle the request.'''

		# check if the request is a TLS request
		sock = pyHandler.request
		if not isinstance(sock, ssl.SSLSocket):
			pyHandler.LogDebug('TLS: Not a TLS request.')
			pyHandler.SetCodeAndTextMessage(code=403, message='Forbidden')
			return

		# retrieve the peer certificate chain
		peerCertChainDER = sock.get_verified_chain()
		peerCertChain: list[Certificate] = []
		try:
			for cert in peerCertChainDER:
				peerCertChain.append(load_der_x509_certificate(cert))
		except:
			# the peer certificate chain is not valid
			pyHandler.LogDebug('TLS: failed to load peer certificate chain.')
			pyHandler.SetCodeAndTextMessage(code=403, message='Forbidden')
			return

		if len(peerCertChain) == 0:
			# the peer certificate chain is empty
			pyHandler.LogDebug('TLS: empty peer certificate chain.')
			pyHandler.SetCodeAndTextMessage(code=403, message='Forbidden')
			return

		try:
			rootCaCert = self._FindRootCaCert(
				certChain=peerCertChain,
				trustedCerts=self._rootCaCerts,
			)
			if rootCaCert is None:
				raise RuntimeError('Cannot find the root CA cert.')

			certChain, errMsg = self._VerifyCertChain(
				certChain=peerCertChain,
				trustedCert=rootCaCert,
			)
			if errMsg is not None:
				raise RuntimeError(errMsg)
			if len(certChain) == 0:
				raise RuntimeError('The certificate chain is empty.')

			leafCert = certChain[0]

			# store the peer certificate chain in the request state
			reqState['peer_cert'] = leafCert
			reqState['peer_intermediate_cert'] = certChain[1:]
			reqState['peer_root_cert'] = rootCaCert

			# get common name and subject alternative name from the leaf cert
			leafSubj = leafCert.subject
			commonName = leafSubj.get_attributes_for_oid(
				x509NameOID.COMMON_NAME,
			)[0].value
			leafCertExt = leafCert.extensions
			subjAltName = leafCertExt.get_extension_for_class(x509SubjectAlternativeName).value.get_values_for_type(x509DNSName)

			reqState['peer_common_name'] = commonName
			reqState['peer_alt_name'] = subjAltName
		except Exception as e:
			# the peer certificate chain is not valid
			pyHandler.LogDebug('TLS: failed to verify peer certificate chain: %s.', e)
			pyHandler.SetCodeAndTextMessage(code=403, message='Forbidden')
			return

		self._downstreamHTTPHdlr.HandleRequest(
			host=host,
			relPath=relPath,
			pyHandler=pyHandler,
			handlerState=handlerState,
			reqState=reqState,
			terminateEvent=terminateEvent,
		)

