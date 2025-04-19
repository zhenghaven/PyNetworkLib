#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import ipaddress
import threading

from ..DownstreamHandlerBase import DownstreamHandlerBase
from ..PreHandler import PreHandler
from ..Utils.HandlerState import HandlerState
from ..Utils.HostField import HOST_FIELD_TYPES


_IPNETWORK_TYPES = ipaddress.IPv4Network | ipaddress.IPv6Network


class IPNetwork(DownstreamHandlerBase):
	'''A authentication/authorization handler that limits the source IP
	to a specific network.
	'''

	def __init__(
		self,
		ipNetworks: list[tuple[_IPNETWORK_TYPES, bool]],
		downstreamHTTPHdlr: DownstreamHandlerBase,
	) -> None:
		'''
		Constructor for the IPNetwork class.
		'''

		super().__init__()
		self._ipNetworks = ipNetworks

		self._downstreamHTTPHdlr = downstreamHTTPHdlr

	def _GetPolicyByIP(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
		'''Get the policy by IP address.'''

		for network, policy in self._ipNetworks:
			if ip in network:
				return policy

		# If no network matches, return False (deny access)
		return False

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

		# Get the source IP address
		srcIPStr = pyHandler.client_address[0]
		srcIP = ipaddress.ip_address(srcIPStr)

		isAllowed = self._GetPolicyByIP(srcIP)
		if not isAllowed:
			pyHandler.LogDebug(
				'IPNetwork: IP %s is not allowed; access denied.',
				srcIPStr,
			)
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

