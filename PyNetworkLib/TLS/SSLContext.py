#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import datetime
import logging
import os
import secrets
import socket
import ssl

from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes, PublicKeyTypes
from cryptography.hazmat.primitives.serialization import (
	Encoding,
	PrivateFormat,
	PublicFormat,
	BestAvailableEncryption,
	load_pem_private_key,
)
from cryptography.x509.base import Certificate, load_pem_x509_certificates


def PubKeyToRawBytes(pubKey: PublicKeyTypes) -> bytes:
	'''Convert the public key to raw bytes.'''
	return pubKey.public_bytes(
		encoding = Encoding.DER,
		format   = PublicFormat.SubjectPublicKeyInfo,
	)


class SSLContext:
	'''SSL context is a wrapper around the ssl.SSLContext class.

	It provides more helpful methods for SSL context.
	'''

	@classmethod
	def CreateDefaultContext(
		cls,
		isServerSide: bool,
		caPEMorDER: str | bytes,
		isVerifyRequired: bool=True,
	) -> 'SSLContext':
		'''Create a SSL context with default configurations.

		:param isServerSide: Whether the context is server side or client side.
		:return: The SSL context.
		'''
		# create the SSL context
		purpose = ssl.Purpose.SERVER_AUTH
		if isServerSide:
			# server side; we need to verify the client certificate
			purpose = ssl.Purpose.CLIENT_AUTH

		pySslCtx = ssl.create_default_context(
			purpose=purpose,
			cadata=caPEMorDER,
		)

		# set the default SSL version to TLSv1.3
		pySslCtx.minimum_version = ssl.TLSVersion.TLSv1_3

		# set the verify mode
		pySslCtx.verify_mode = ssl.CERT_REQUIRED
		if not isVerifyRequired:
			# if the verify mode is not required, set it to OPTIONAL
			pySslCtx.verify_mode = ssl.CERT_OPTIONAL

		# create the SSL context
		sslCtx = cls(
			pySslCtx=pySslCtx,
		)
		return sslCtx

	def __init__(
		self,
		pySslCtx: ssl.SSLContext,
	) -> None:
		'''Initialize the SSL context.

		:param pySslCtx: The Python SSL context to wrap.
		'''

		self._logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

		self._pySslCtx = pySslCtx

		# to ensure highest security, TLSv1.3 is used by default.
		self._pySslCtx.minimum_version = ssl.TLSVersion.TLSv1_3

		# the certificate and private key have not been loaded yet
		# so the expires_at is set to minimum datetime
		self._expiresAt = datetime.datetime(
			year=datetime.MINYEAR,
			month=1,
			day=1,
			tzinfo=datetime.timezone.utc,
		)
		self._privKeyPath = None
		self._certChainPath = None
		self._password = None

	def EnableTlsV1_2(self) -> None:
		'''Enable TLSv1.2.

		This lowers the security of the SSL context from TLSv1.3 to TLSv1.2.
		It is used for compatibility with older servers/clients.
		'''
		self._pySslCtx.minimum_version = ssl.TLSVersion.TLSv1_2

	def WrapSocket(
		self,
		sock: socket.socket,
		server_side: bool,
		do_handshake_on_connect: bool=True,
		suppress_ragged_eofs: bool=True,
		server_hostname: str | None=None,
		session=None,
	) -> ssl.SSLSocket:
		'''Wrap a socket with the SSL context.

		:param sock: The socket to wrap.
		:param server_side: Whether the socket is server side or client side.
		:param do_handshake_on_connect: Whether to do handshake on connect.
		:param suppress_ragged_eofs: Whether to suppress ragged EOFs.
		:param server_hostname: The server hostname to use.
		:param session: The session to use.
		:return: The wrapped socket.
		'''

		return self._pySslCtx.wrap_socket(
			sock,
			server_side=server_side,
			do_handshake_on_connect=do_handshake_on_connect,
			suppress_ragged_eofs=suppress_ragged_eofs,
			server_hostname=server_hostname,
			session=session,
		)

	def LoadVerifyCACerts(self, caPEMorDER: str | bytes) -> None:
		'''Load the CA certificates for the SSL context.

		:param caPEMorDER: The CA certificates in PEM or DER format.
		'''
		self._pySslCtx.load_verify_locations(cadata=caPEMorDER)

	def _LoadCertInfo(
		self,
		certChainPath: os.PathLike,
	) -> None:
		'''Load the certificate info from the given file.

		:param certChainPath: The path to the certificate chain file.
		'''
		try:
			with open(certChainPath, 'rb') as f:
				certData = f.read()

			cert = load_pem_x509_certificates(certData)
		except Exception as e:
			self._logger.error('Failed to load the certificate chain: %s', e)
			return

		if len(cert) < 1:
			self._logger.error('The certificate chain is empty.')

		# we assume cert[0] is the server certificate
		svrCert = cert[0]

		# get the expiresAt from the certificate
		self._expiresAt = svrCert.not_valid_after_utc

		expireAtStr = self._expiresAt.strftime('%Y-%m-%d %H:%M:%S')
		self._logger.info(
			'The expiration date of the certificate is %s UTC.',
			expireAtStr,
		)

	def LoadCertChainFiles(
		self,
		certChainPath: os.PathLike,
		privKeyPath: os.PathLike,
		password: str | bytes | None=None,
	) -> None:
		'''Load the private key and certificate chain from the given files.

		:param privKeyPath: The path to the private key file.
		:param certChainPath: The path to the certificate chain file.
		:param password: The password for the private key file.
			(`None` if the private key is not encrypted.)
		'''
		self._certChainPath = certChainPath
		self._privKeyPath = privKeyPath
		self._password = password
		self._LoadCertInfo(certChainPath)

		self._pySslCtx.load_cert_chain(
			certfile=certChainPath,
			keyfile=privKeyPath,
			password=password,
		)

	def LoadCertChain(
		self,
		privKey: PrivateKeyTypes,
		certChain: list[Certificate],
		tmpDir: os.PathLike,
	) -> None:
		'''Load the private key and certificate chain from the given values.

		:param privKey: The private key to use.
		:param certChain: The certificate chain to use.
		:param tmpDir: The temporary directory to use; due to the issue that
			the Python SSL context does not support loading private key and
			certificate chain from memory, we need to write them to a temporary
			file and load them from there.
			NOTE: the private key will be encrypted with a 1024-bit randomly
			generated key by default before writing to the file.
		'''
		# check if the private key corresponds to the first certificate in the chain
		if len(certChain) < 1:
			raise ValueError('The certificate chain is empty.')
		for cert in certChain:
			if not isinstance(cert, Certificate):
				raise ValueError('The certificate chain is not a list of certificates.')
		if not isinstance(privKey, PrivateKeyTypes):
			raise ValueError('The private key is not a valid private key.')
		if PubKeyToRawBytes(privKey.public_key()) != PubKeyToRawBytes(certChain[0].public_key()):
		# if privKey.public_key().public_bytes_raw() != certChain[0].public_key().public_bytes_raw():
			raise ValueError('The private key does not correspond to the first certificate in the chain.')

		# generate a random file name
		randFilename = secrets.token_hex(16)
		randKeyFilePath = os.path.join(tmpDir, f'{randFilename}.priv')
		randCertFilePath = os.path.join(tmpDir, f'{randFilename}.cert')

		# generate a random password for the private key
		privKeyPass = secrets.token_urlsafe(128)
		# generate private key PEM
		privPEM = privKey.private_bytes(
			encoding = Encoding.PEM,
			format   = PrivateFormat.PKCS8,
			encryption_algorithm = BestAvailableEncryption(privKeyPass.encode())
		).decode()

		# generate certificate chain PEM
		certChainPEM = ''
		for cert in certChain:
			certChainPEM += cert.public_bytes(Encoding.PEM).decode()
			if certChainPEM[-1] != '\n':
				certChainPEM += '\n'

		# write the private key and certificate chain to the temporary files
		privKeyFileDesp = os.open(
			randKeyFilePath,
			flags=os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
			mode=0o600
		)
		with open(privKeyFileDesp, 'w') as f:
			f.write(privPEM)

		# write the certificate chain to the temporary files
		with open(randCertFilePath, 'w') as f:
			f.write(certChainPEM)

		# load the private key and certificate chain from the temporary files
		self.LoadCertChainFiles(
			certChainPath=randCertFilePath,
			privKeyPath=randKeyFilePath,
			password=privKeyPass
		)

	def SetVerifyModeCertRequired(self) -> None:
		'''Set the verify mode to CERT_REQUIRED.'''
		self._pySslCtx.verify_mode = ssl.CERT_REQUIRED

	def SetVerifyModeCertOptional(self) -> None:
		'''Set the verify mode to CERT_OPTIONAL.'''
		self._pySslCtx.verify_mode = ssl.CERT_OPTIONAL

	def SetVerifyModeCertNone(self) -> None:
		'''Set the verify mode to CERT_NONE.'''
		self._pySslCtx.verify_mode = ssl.CERT_NONE

	def HasCertExpired(
		self,
		adjustment: datetime.timedelta | None=datetime.timedelta(days=1)
	) -> bool:
		'''Check if the certificate has expired.

		:return: True if the certificate has expired, False otherwise.
		'''
		if adjustment is None:
			adjustment = datetime.timedelta(days=0)

		# make the adjustment to the expiresAt to make it "expires" earlier
		# than the actual expiresAt
		adjustedExpiresAt = self._expiresAt - adjustment

		return datetime.datetime.now(datetime.timezone.utc) > adjustedExpiresAt

	def ReloadCertChainFilesIfExpired(self) -> bool:
		'''Reload the certificate chain if it has expired.

		:return: True if a newer certificate chain is loaded, False otherwise.
		'''
		if self._certChainPath is None:
			self._logger.error(
				'The certificate chain path is not set. Cannot reload the certificate chain.'
			)
			return False

		if self.HasCertExpired():
			self._logger.info(
				'The certificate has expired, reloading the certificate chain.'
			)
			self.LoadCertChainFiles(
				certChainPath=self._certChainPath,
				privKeyPath=self._privKeyPath,
				password=self._password,
			)
			if self.HasCertExpired():
				self._logger.error(
					'Failed to reload the certificate chain. The certificate is still expired.'
				)
				return False
			self._logger.info(
				'A newer certificate chain has been loaded successfully.'
			)

		return True

