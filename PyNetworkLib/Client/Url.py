#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import ipaddress


def GenUrlPrefix(
	scheme: str,
	*,
	port: int | None = None,
	hostname: str | None = None,
	ip: str | None = None,
) -> str:
	if hostname is None and ip is None:
		raise ValueError('Either hostname or ip must be provided.')

	if ip is not None:
		# we prefer to use the ip address
		ipAddr = ipaddress.ip_address(ip)
		if ipAddr.version == 4:
			hostStr = str(ipAddr)
		elif ipAddr.version == 6:
			hostStr = f'[{ipAddr}]'
		else:
			raise ValueError('Unsupported IP version.')
	else:
		# ip is None, use hostname
		hostStr = hostname

	if port is not None:
		# port is provided, append it to the host string
		hostStr = f'{hostStr}:{port}'

	return f'{scheme}://{hostStr}'


def GenHTTPUrlPrefix(
	*,
	port: int | None = None,
	hostname: str | None = None,
	ip: str | None = None,
) -> str:
	return GenUrlPrefix(
		scheme='http',
		port=port,
		hostname=hostname,
		ip=ip,
	)

def GenHTTPSUrlPrefix(
	*,
	port: int | None = None,
	hostname: str | None = None,
	ip: str | None = None,
) -> str:
	return GenUrlPrefix(
		scheme='https',
		port=port,
		hostname=hostname,
		ip=ip,
	)

