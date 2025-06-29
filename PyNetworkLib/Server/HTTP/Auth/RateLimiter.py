#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import threading
import time

from collections import deque

from ...Utils.HandlerState import HandlerState
from ..DownstreamHandlerBase import DownstreamHandlerBase
from ..PreHandler import PreHandler
from ..Utils.HostField import HOST_FIELD_TYPES


class RateLimiter(DownstreamHandlerBase):
	'''A concurrent limiter that limits the number of concurrent requests
	being handled.
	'''

	def __init__(
		self,
		maxReq: int,
		timePeriodSec: float,
		downstreamHTTPHdlr: DownstreamHandlerBase,
	) -> None:
		'''
		Constructor for the RateLimiter class.
		'''

		super().__init__()

		self._maxReq = maxReq
		self._timePeriodSec = timePeriodSec

		self._reqTimesLock = threading.Lock()
		self._reqTimes = deque()

		self._downstreamHTTPHdlr = downstreamHTTPHdlr

	@property
	def maxNumRequestsPerPeriod(self) -> int:
		'''Get the maximum number of requests per time period.'''
		return self._maxReq

	def _CheckRateLimit(self) -> bool:
		'''Check if the rate limit is exceeded.'''
		now = time.time()
		with self._reqTimesLock:
			while (
				self._reqTimes
				and (now - self._reqTimes[0]) > self._timePeriodSec
			):
				# remove timestamps that are older than the time period
				self._reqTimes.popleft()

			# check if the rate limit is exceeded
			if len(self._reqTimes) >= self.maxNumRequestsPerPeriod:
				return False

			# add the current timestamp to the deque
			self._reqTimes.append(now)
			return True

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

		# check if the rate limit is exceeded
		rateLimitRes = self._CheckRateLimit()

		if rateLimitRes:
			# handle the request
			self._downstreamHTTPHdlr.HandleRequest(
				host=host,
				relPath=relPath,
				pyHandler=pyHandler,
				handlerState=handlerState,
				reqState=reqState,
				terminateEvent=terminateEvent,
			)
		else:
			# rate limit exceeded
			pyHandler.LogDebug(
				'ConcurrentLimiter: Rate limit exceeded. '
				'Request denied.',
			)
			pyHandler.SetCodeAndTextMessage(
				code=403,
				message='Forbidden',
			)

