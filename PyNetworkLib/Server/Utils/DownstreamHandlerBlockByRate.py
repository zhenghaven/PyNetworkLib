#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import collections
import ipaddress
import json
import os
import logging
import threading
import time

from typing import Any


IP_ADDRESS_TYPES = ipaddress.IPv4Address | ipaddress.IPv6Address


class BlockedState:
	'''
	A class to represent the blocked state of IP addresses and networks.
	'''

	def __init__(self, serializedState: dict = dict()):
		'''
		Constructor for the BlockedState class.

		The serialized state is a dictionary in the following format:
		```JSON
		{
			'hosts': [
				{
					'ip': '::1',
					'timestamp': 1700000000.0,
				}
			],
			'networks': [
				{
					'net': '2001:db8::/32',
				}
			]
		}
		```

		:param serializedState: A dictionary representing the serialized state.
		'''
		self._logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

		self._hosts = {}
		serializedHosts = serializedState.get('hosts', [])
		for host in serializedHosts:
			assert isinstance(host, dict), 'Host must be a dictionary.'
			assert 'ip' in host, 'Host must contain an "ip" key.'
			assert 'timestamp' in host, 'Host must contain a "timestamp" key.'
			ip = ipaddress.ip_address(host['ip'])
			timestamp = host['timestamp']
			self._hosts[ip] = {
				'timestamp': float(timestamp),
			}

		self._networks = {}
		serializedNetworks = serializedState.get('networks', [])
		for network in serializedNetworks:
			assert isinstance(network, dict), 'Network must be a dictionary.'
			assert 'net' in network, 'Network must contain a "net" key.'
			net = ipaddress.ip_network(network['net'], strict=False)
			self._networks[net] = {}

	def IsIpBlocked(self, ipObj: IP_ADDRESS_TYPES) -> bool:
		'''
		Check if the IP address is blocked.

		:param ip: The IP address to check.
		:return: True if the IP address is blocked, False otherwise.
		'''
		return (ipObj in self._hosts) or any(
			ipObj in net for net in self._networks
		)

	def AddHost(
		self,
		ipObj: IP_ADDRESS_TYPES,
		timestamp: float | None = None,
	) -> None:
		'''
		Add a host to the blocked state.

		:param ip: The IP address to add.
		:param timestamp: The timestamp when the host was added. If None,
			the current time is used.
		'''
		if timestamp is None:
			timestamp = time.time()

		self._hosts[ipObj] = {'timestamp': timestamp}

	def AddNetwork(self, net: str) -> None:
		'''
		Add a network to the blocked state.

		:param net: The network to add in CIDR notation.
		'''
		netObj = ipaddress.ip_network(net, strict=False)

		self._networks[netObj] = {}

	def Serialize(self) -> dict:
		'''
		Serialize the blocked state to a dictionary.

		:return: A dictionary representing the blocked state.
		'''
		hosts = [
			{'ip': str(ip), 'timestamp': float(data['timestamp'])}
			for ip, data in self._hosts.items()
		]
		networks = [
			{'net': str(net)} for net in self._networks.keys()
		]

		return {
			'hosts': hosts,
			'networks': networks,
		}

	def DeepCopy(self) -> 'BlockedState':
		'''
		Create a deep copy of the blocked state.

		:return: A new BlockedState object with the same data.
		'''
		return BlockedState(serializedState=self.Serialize())


class DownstreamHandlerBlockByRate:
	'''
	Downstream handler that blocks the request if the rate of requests
	from the same IP address exceeds a certain threshold.
	'''

	def __init__(
		self,
		maxNumRequests: int,
		timeWindowSec: float,
		downstreamHandler: Any,
		savedStatePath: None | os.PathLike = None,
	):
		'''
		Constructor for the downstream handler that blocks requests by rate.
		An optional savedStatePath can be provided to load and save the
		state of the handler.


		:param maxNumRequests: The maximum number of requests allowed from the
			same IP address within the time window.
		:param timeWindowSec: The time window in seconds within which the
			number of requests is counted.
		:param savedState: The path to the file where the state of the
			handler is saved. If None, the state is not loaded or saved.
		'''

		self._maxNumRequests = maxNumRequests
		self._timeWindowSec = timeWindowSec
		self._downstreamHandler = downstreamHandler
		self._savedStatePath = savedStatePath

		self._blockedState = BlockedState()
		self._blockedStateLock = threading.Lock()

		self._requesterList = collections.deque()
		self._requesterCounter = dict()
		self._requesterRecordLock = threading.Lock()

		self._logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

		if self._savedStatePath is not None:
			if not os.path.exists(self._savedStatePath):
				savedStateDir = os.path.dirname(self._savedStatePath)
				if not os.path.exists(savedStateDir):
					raise FileNotFoundError(
						f'Saved state directory {savedStateDir} does not exist.'
					)

				self._logger.warning(
					f'Saved state file {self._savedStatePath} does not exist. '
					'will create a new one when saving the state.'
				)
			else:
				self._LoadSavedState()

	def _LoadSavedState(self) -> None:
		'''Load the saved state from the file.'''

		with open(self._savedStatePath, 'r') as f:
			# Load the state from the file
			newBlockedState = BlockedState(serializedState=json.load(f))

			with self._blockedStateLock:
				self._blockedState = newBlockedState
				self._logger.info(
					f'Loaded saved state from {self._savedStatePath}.'
				)

	def _WriteSavedState(self) -> None:
		'''Write the saved state to the file.'''

		with open(self._savedStatePath, 'w') as f:
			with self._blockedStateLock:
				serializedState = self._blockedState.Serialize()

			json.dump(serializedState, f, indent=4)
			self._logger.info(
				f'Saved state to {self._savedStatePath}.'
			)

	def IsIpBlocked(self, ip: str) -> bool:
		'''Check if the IP address is blocked.'''
		try:
			ipObj = ipaddress.ip_address(ip)
		except ValueError:
			self._logger.error(f'Invalid IP address: {ip}')
			# by default, we block invalid IP addresses
			return True

		with self._blockedStateLock:
			stateCheckRes = self._blockedState.IsIpBlocked(ipObj=ipObj)

		# update the requester record before returning the result
		self._CheckRequesterRecord(ipObj)

		return stateCheckRes

	def _CheckRequesterRecord(self, ipObj: IP_ADDRESS_TYPES) -> None:
		'''
		Check the requester record and update the blocked state if necessary.
		'''

		currentTime = time.time()
		with self._requesterRecordLock:
			# Remove old requests from the requester list
			while (
				self._requesterList # not empty
				and (
					(currentTime - self._requesterList[0][1]) > self._timeWindowSec
				) # the oldest request is outside the time window
			):
				# Remove the oldest request from the requester list
				oldIp, _ = self._requesterList.popleft()
				self._requesterCounter[oldIp] -= 1
				if self._requesterCounter[oldIp] <= 0:
					del self._requesterCounter[oldIp]

			# Add the current request to the requester list
			self._requesterList.append((ipObj, currentTime))
			if ipObj not in self._requesterCounter:
				self._requesterCounter[ipObj] = 0
			self._requesterCounter[ipObj] += 1

			# Check if the number of requests exceeds the limit
			if self._requesterCounter[ipObj] > self._maxNumRequests:
				self._logger.warning(
					f'IP {ipObj} has exceeded the maximum number of requests '
					f'({self._maxNumRequests}) within the time window '
					f'({self._timeWindowSec} seconds). Blocking the IP.'
				)
				with self._blockedStateLock:
					self._blockedState.AddHost(ipObj, currentTime)

				if self._savedStatePath is not None:
					self._WriteSavedState()

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

		if self.IsIpBlocked(clientIP):
			# This IP address is blocked, do not handle the request
			return

		return self._downstreamHandler.HandleRequest(reqState=reqState, **kwargs)

