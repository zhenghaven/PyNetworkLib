#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import hashlib
import secrets


def CalcHashedTotpToken(
	currTotp: str,
	randomSalt: str,
) -> str:
	return hashlib.sha512(
		(randomSalt + ':' + currTotp).encode('utf-8')
	).hexdigest()


def GenTotpToken(currTotp: str) -> str:
	randomSalt = secrets.token_hex(32)
	return randomSalt + ':' + CalcHashedTotpToken(
		currTotp=currTotp,
		randomSalt=randomSalt
	)

