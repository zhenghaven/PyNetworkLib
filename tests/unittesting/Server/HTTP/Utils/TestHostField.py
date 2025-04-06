#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import ipaddress
import unittest


from PyNetworkLib.Server.HTTP.Utils.HostField import (
	HostFieldBase,
	HostFieldDomain,
	HostFieldIPV4,
	HostFieldIPV6,
	ParseHostField,
	Type as HostFieldType,
)


class TestHostField(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_Server_HTTP_Utils_HostField_01ParseDomain(self):
		# a valid domain name
		domain = 'www.example.com'
		defPort = 443

		hostField = ParseHostField(domain, defPort)
		self.assertIsInstance(hostField, HostFieldBase)
		self.assertIsInstance(hostField, HostFieldDomain)
		self.assertEqual(hostField.fieldType, HostFieldType.DOMAIN)
		self.assertEqual(hostField.domain, domain)
		self.assertEqual(hostField.port, defPort)
		self.assertEqual(f'{hostField}', f'{domain}:{defPort}')
		self.assertEqual(str(hostField), f'{domain}:{defPort}')

		# a valid domain name with a port
		domain = 'www.example.com:8443'
		defPort = 443

		hostField = ParseHostField(domain, defPort)
		self.assertIsInstance(hostField, HostFieldBase)
		self.assertIsInstance(hostField, HostFieldDomain)
		self.assertEqual(hostField.fieldType, HostFieldType.DOMAIN)
		self.assertEqual(hostField.domain, 'www.example.com')
		self.assertEqual(hostField.port, 8443)
		self.assertEqual(f'{hostField}', f'{domain}')
		self.assertEqual(str(hostField), f'{domain}')

		# invalid domain names
		defPort = 443
		domain = 'invalid_domain'
		with self.assertRaises(ValueError):
			ParseHostField(domain, defPort)
		domain = '@invalid_domain'
		with self.assertRaises(ValueError):
			ParseHostField(domain, defPort)
		domain = 'invalidport:12ab'
		with self.assertRaises(ValueError):
			ParseHostField(domain, defPort)

	def test_Server_HTTP_Utils_HostField_02ParseIPV4(self):
		# a valid IPv4 address
		ipv4Addr = '192.168.0.1'
		defPort = 80

		hostField = ParseHostField(ipv4Addr, defPort)
		self.assertIsInstance(hostField, HostFieldBase)
		self.assertIsInstance(hostField, HostFieldIPV4)
		self.assertEqual(hostField.fieldType, HostFieldType.IPV4)
		self.assertEqual(hostField.ip, ipaddress.IPv4Address(ipv4Addr))
		self.assertEqual(hostField.port, defPort)
		self.assertEqual(f'{hostField}', f'{ipv4Addr}:{defPort}')
		self.assertEqual(str(hostField), f'{ipv4Addr}:{defPort}')

		# a valid IPv4 address with a port
		ipv4Addr = '192.168.0.255:8080'
		defPort = 80

		hostField = ParseHostField(ipv4Addr, defPort)
		self.assertIsInstance(hostField, HostFieldBase)
		self.assertIsInstance(hostField, HostFieldIPV4)
		self.assertEqual(hostField.fieldType, HostFieldType.IPV4)
		self.assertEqual(hostField.ip, ipaddress.IPv4Address(ipv4Addr.split(':')[0]))
		self.assertEqual(hostField.port, 8080)
		self.assertEqual(f'{hostField}', f'{ipv4Addr}')
		self.assertEqual(str(hostField), f'{ipv4Addr}')

		# invalid IPv4 addresses
		defPort = 80
		ipv4Addr = '192.168.abc.1'
		with self.assertRaises(ValueError):
			ParseHostField(ipv4Addr, defPort)
		ipv4Addr = '192.168.0.256'
		with self.assertRaises(ValueError):
			ParseHostField(ipv4Addr, defPort)
		ipv4Addr = '192.168.0.1:12ab'
		with self.assertRaises(ValueError):
			ParseHostField(ipv4Addr, defPort)

	def test_Server_HTTP_Utils_HostField_03ParseIPV6(self):
		# a valid IPv6 address
		ipv6Addr = '[fd00:0000:0000:0000:0000:0000:0000:0001]'
		defPort = 80

		hostField = ParseHostField(ipv6Addr, defPort)
		self.assertIsInstance(hostField, HostFieldBase)
		self.assertIsInstance(hostField, HostFieldIPV6)
		self.assertEqual(hostField.fieldType, HostFieldType.IPV6)
		self.assertEqual(hostField.ip, ipaddress.IPv6Address(ipv6Addr[1:-1]))
		self.assertEqual(hostField.port, defPort)
		self.assertEqual(f'{hostField}', f'[{ipaddress.IPv6Address(ipv6Addr[1:-1])}]:{defPort}')
		self.assertEqual(str(hostField), f'[{ipaddress.IPv6Address(ipv6Addr[1:-1])}]:{defPort}')

		# a valid IPv6 address with a port
		ipv6Addr = '[fd00::0001]:8080'
		defPort = 80

		hostField = ParseHostField(ipv6Addr, defPort)
		self.assertIsInstance(hostField, HostFieldBase)
		self.assertIsInstance(hostField, HostFieldIPV6)
		self.assertEqual(hostField.fieldType, HostFieldType.IPV6)
		self.assertEqual(hostField.ip, ipaddress.IPv6Address('fd00::0001'))
		self.assertEqual(hostField.port, 8080)
		self.assertEqual(f'{hostField}', f'[fd00::1]:8080')
		self.assertEqual(str(hostField), f'[fd00::1]:8080')

		# invalid IPv6 addresses
		defPort = 80
		ipv6Addr = 'fd00:0000:0000:0000:0000:0000:0000:0001'
		with self.assertRaises(ValueError):
			ParseHostField(ipv6Addr, defPort)
		ipv6Addr = '[fd00:0000:0000:0000:0000:0000:0000:0001'
		with self.assertRaises(ValueError):
			ParseHostField(ipv6Addr, defPort)
		ipv6Addr = '[fd00:abcd:efgh::0001]'
		with self.assertRaises(ValueError):
			ParseHostField(ipv6Addr, defPort)
		ipv6Addr = '[fd00:0000:0000:0000:0000:0000:0000:0001]:12ab'
		with self.assertRaises(ValueError):
			ParseHostField(ipv6Addr, defPort)

