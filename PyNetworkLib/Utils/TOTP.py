#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2022 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


# TOTP and HOTP reference: https://github.com/google/google-authenticator/wiki/Key-Uri-Format
# RFC 6238: https://tools.ietf.org/html/rfc6238

import base64
import hmac
import secrets
import struct
import time
from typing import Union


ALLOWED_DIGESTS = [
	'sha1',
	'sha256',
	'sha512'
]


def _hotp(
	key: str,
	counter: int,
	digits: int = 6,
	digest: str = 'sha1'
) -> str:
	key = base64.b32decode(key.upper() + '=' * ((8 - len(key)) % 8))
	counter = struct.pack('>Q', counter)
	mac = hmac.new(key, counter, digest).digest()
	offset = mac[-1] & 0x0f
	binary = struct.unpack('>L', mac[offset:offset+4])[0] & 0x7fffffff
	return str(binary)[-digits:].zfill(digits)


def _totp(
	key: str,
	time_step: int = 30,
	digits: int = 6,
	digest: str = 'sha1'
) -> str:
	return _hotp(key, int(time.time() / time_step), digits, digest)


def _generate_secret(length=16):
	return base64.b32encode(
		secrets.token_bytes(nbytes=length)
	).decode().replace('=', '')


class Totp(object):

	def __init__(
		self,
		secret: Union[str, None],
		secretLen: Union[int, None] = None,
		timeStep: int = 30,
		digits: int = 6,
		digest: str = 'sha1',
		accountName: Union[str, None] = None,
		issuer: Union[str, None] = None
	) -> None:
		super(Totp, self).__init__()

		if digest not in ALLOWED_DIGESTS:
			raise ValueError('Invalid digest')

		if (((secret is None) and (secretLen is None)) or
			((secret is not None) and (secretLen is not None))):
			raise ValueError('Only one of secret and secretLen can be specified')

		if digits not in [6, 8]:
			raise ValueError('Invalid digits length')

		if secret is None:
			# generate a new secret
			secret = _generate_secret(secretLen)

		self.secret = secret
		self.timeStep = timeStep
		self.digits = digits
		self.digest = digest
		self.accountName = accountName
		self.issuer = issuer


	def GetOtpAuth(self) -> str:
		if ((self.issuer is None) or
			(self.accountName is None)):
			raise ValueError('Missing issuer, account name, or both')

		otpAuth = '\
otpauth://totp/{issuer}:{accName}?\
secret={secret}&\
issuer={issuer}&\
digits={digits}&\
period={period}&\
algorithm={digest}'.format(
			issuer=self.issuer,
			accName=self.accountName,
			secret=self.secret,
			digits=self.digits,
			period=self.timeStep,
			digest=self.digest.upper()
		)
		return otpAuth

	def Now(self) -> str:
		return _totp(
			key=self.secret,
			time_step=self.timeStep,
			digits=self.digits,
			digest=self.digest
		)

