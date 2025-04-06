#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import threading

from ..DownstreamHandlerBase import DownstreamHandlerBase
from ..PreHandler import PreHandler
from ..Utils.HandlerState import HandlerState
from ..Utils.HostField import HOST_FIELD_TYPES


class ConcurrentLimiter(DownstreamHandlerBase):
	'''A concurrent limiter that limits the number of concurrent requests
	being handled.
	'''

	def __init__(
		self,
		maxConcurrent: int,
		downstreamHTTPHdlr: DownstreamHandlerBase,
	) -> None:
		'''
		Constructor for the RateLimiter class.
		'''

		super().__init__()
		self._semaphore = threading.Semaphore(maxConcurrent)
		self._maxConcurrent = maxConcurrent

		self._downstreamHTTPHdlr = downstreamHTTPHdlr

	def HandleRequest(
		self,
		host: HOST_FIELD_TYPES,
		relPath: str,
		pyHandler: PreHandler,
		state: HandlerState,
		terminateEvent: threading.Event,
	) -> None:
		'''Handle the request.'''

		hasAllowance = self._semaphore.acquire(blocking=False)
		if not hasAllowance:
			pyHandler.LogDebug(
				'ConcurrentLimiter: Too many concurrent requests. '
				'Request denied.',
			)
			pyHandler.SetCodeAndTextMessage(
				code=403,
				message='Forbidden',
			)
			return

		try:
			self._downstreamHTTPHdlr.HandleRequest(
				host=host,
				relPath=relPath,
				pyHandler=pyHandler,
				state=state,
				terminateEvent=terminateEvent,
			)
		finally:
			self._semaphore.release()
			# release the semaphore in the finally block to ensure it is released
			# even if the downstream handler raises an exception

