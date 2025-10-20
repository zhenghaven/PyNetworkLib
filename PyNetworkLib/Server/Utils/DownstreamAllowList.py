#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import ipaddress
import json
import logging
import os

from typing import Any


class DownstreamAllowList:
	'''
	Downstream handler that blocks the request if the IP address is not in the
	allow list.
	'''

	def __init__(
		self,
		allowListOrFile: os.PathLike | list[str],
		downstreamHandler: Any,
		logIPs: bool = False,
	):
		'''
		Constructor for the downstream handler that blocks requests from IP
		addresses not in the allow list.

		:param allowListOrFile: The path to the allow list file or a list of
			allowed IP addresses/CIDR ranges in string format.
		:param downstreamHandler: The downstream handler to delegate to if
			the request is not blocked.
		:param logIPs: Whether to log the IP addresses of incoming requests.
		'''

		if isinstance(allowListOrFile, list):
			self._allowList = [ipaddress.ip_network(ipStr) for ipStr in allowListOrFile]
		else:
			if not os.path.exists(allowListOrFile):
				raise FileNotFoundError(
					f'Allow list file {allowListOrFile} does not exist.'
				)

			with open(allowListOrFile, 'r') as f:
				allowListJson = json.load(f)
			self._allowList = [ipaddress.ip_network(ipStr) for ipStr in allowListJson]

		self._downstreamHandler = downstreamHandler
		self._logIPs = logIPs

		self._blockedIPs = set()

		self._logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

	def IsIpBlocked(self, ip: str) -> bool:
		'''Check if the IP address is blocked.'''
		try:
			ipObj = ipaddress.ip_address(ip)
			if (ipObj.version == 6) and (ipObj.ipv4_mapped is not None):
				ipObj = ipObj.ipv4_mapped  # Convert IPv6-mapped IPv4 to IPv4
		except ValueError:
			self._logger.error('Invalid IP address: %s', ip)
			# by default, we block invalid IP addresses
			return True

		if ipObj in self._blockedIPs:
			return True  # IP is already blocked

		for net in self._allowList:
			if ipObj in net:
				return False  # IP is in the allow list

		# IP is not in the allow list
		if self._logIPs and ipObj not in self._blockedIPs:
			self._logger.info('Blocking request from IP not in allow list: %s', ipObj)
			self._blockedIPs.add(ipObj)

		return True

	def HandleRequest(self, *, reqState: dict, **kwargs) -> None:
		'''
		Handle the request by checking the blocked state and delegating to
		the downstream handler if the request is not blocked.

		:param reqState: The state of the current request.
		'''

		clientIP = reqState.get('clientIP', None)
		if clientIP is None:
			self._logger.error('Client IP address is not provided in reqState.')
			# Block the request if client IP is not provided
			return
		clientPort = reqState.get('clientPort', None)

		if self._logIPs:
			self._logger.debug('Received request from: %s:%s', clientIP, str(clientPort))

		if self.IsIpBlocked(clientIP):
			# This IP address is blocked, do not handle the request
			return

		if self._logIPs:
			self._logger.info('Non-blocked request from: %s:%s', clientIP, str(clientPort))

		return self._downstreamHandler.HandleRequest(reqState=reqState, **kwargs)

