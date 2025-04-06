#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import enum
import ipaddress
import re


class Type(enum.Enum):
	'''The type of the host field.'''

	DOMAIN = 0
	IPV4 = 1
	IPV6 = 2


class HostFieldBase:

	@property
	def fieldType(self) -> Type:
		'''The type of the host field.'''
		raise NotImplementedError('This method should be overridden by subclasses.')


class HostFieldDomain(HostFieldBase):
	'''The host field is a domain name.'''

	def __init__(self, domain: str, port: int):
		super().__init__()

		self._domain = domain
		self._port = port

	@property
	def fieldType(self) -> Type:
		'''The type of the host field.'''
		return Type.DOMAIN

	@property
	def domain(self) -> str:
		'''The domain name.'''
		return self._domain

	@property
	def port(self) -> int:
		'''The port number.'''
		return self._port

	def __str__(self):
		return f'{self._domain}:{self._port}'


class HostFieldIPV4(HostFieldBase):
	'''The host field is an IPv4 address.'''

	def __init__(self, ip: ipaddress.IPv4Address, port: int):
		super().__init__()

		self._ip = ip
		self._port = port

	@property
	def fieldType(self) -> Type:
		'''The type of the host field.'''
		return Type.IPV4

	@property
	def ip(self) -> ipaddress.IPv4Address:
		'''The IPv4 address.'''
		return self._ip

	@property
	def port(self) -> int:
		'''The port number.'''
		return self._port

	def __str__(self):
		return f'{self._ip}:{self._port}'


class HostFieldIPV6(HostFieldBase):
	'''The host field is an IPv6 address.'''

	def __init__(self, ip: ipaddress.IPv6Address, port: int):
		super().__init__()

		self._ip = ip
		self._port = port

	@property
	def fieldType(self) -> Type:
		'''The type of the host field.'''
		return Type.IPV6

	@property
	def ip(self) -> ipaddress.IPv6Address:
		'''The IPv6 address.'''
		return self._ip

	@property
	def port(self) -> int:
		'''The port number.'''
		return self._port

	def __str__(self):
		return f'[{self._ip}]:{self._port}'


HOST_FIELD_TYPES = HostFieldDomain | HostFieldIPV4 | HostFieldIPV6


_DOMAIN_REGEX = re.compile(
	r'^((?:[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\.)+[a-zA-Z]{2,})(:[0-9]+)?$'
)
_IPV4_REGEX = re.compile(
	r'^([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)(:[0-9]+)?$'
)
_IPV6_REGEX = re.compile(
	r'^\[([0-9a-fA-F:]+)\](:[0-9]+)?$'
)


def _DeterminePortNum(
	regexMatch: re.Match,
	portRegexIdx: int,
	defaultPort: int,
) -> int:
	if regexMatch.group(2):
		port = regexMatch.group(2)[1:]
		port = int(port)
	else:
		port = defaultPort

	return port


def ParseHostField(host: str, defaultPort: int) -> HOST_FIELD_TYPES:
	'''Parse the host field from the request header.

	Args:
		host: The host field from the request header.

	Returns:
		The parsed host field.
	'''

	# check if the host field is a domain name
	domainMatch = _DOMAIN_REGEX.match(host)
	if domainMatch:
		domain = domainMatch.group(1)
		port = _DeterminePortNum(domainMatch, 2, defaultPort)
		return HostFieldDomain(domain, port)

	# check if the host field is an IPv4 address
	ipv4Match = _IPV4_REGEX.match(host)
	if ipv4Match:
		ip = ipaddress.IPv4Address(ipv4Match.group(1))
		port = _DeterminePortNum(ipv4Match, 2, defaultPort)
		return HostFieldIPV4(ip, port)

	# check if the host field is an IPv6 address
	ipv6Match = _IPV6_REGEX.match(host)
	if ipv6Match:
		ip = ipaddress.IPv6Address(ipv6Match.group(1))
		port = _DeterminePortNum(ipv6Match, 2, defaultPort)
		return HostFieldIPV6(ip, port)

	raise ValueError(f'Invalid host field: {host}')

