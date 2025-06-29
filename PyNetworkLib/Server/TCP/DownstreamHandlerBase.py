#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import threading

from ..Utils.HandlerState import HandlerState
from .PyHandlerBase import PyHandlerBase


class DownstreamHandlerBase:
	'''
	Base class for all downstream handler classes.
	'''

	def __init__(self):
		'''
		Constructor for the downstream handler class.
		'''

	def HandleRequest(
		self,
		pyHandler: PyHandlerBase,
		handlerState: HandlerState,
		reqState: dict,
		terminateEvent: threading.Event,
	) -> None:
		'''Handle the request.

		:param pyHandler: The TCP request handler object.
		:param handlerState: The state of the handler of a server shared by
			all requests made to that server.
		:param reqState: The state of the current request.
		:param terminateEvent: The event that is set when the server is
			terminated.
		'''

		raise NotImplementedError(
			'Handle() method must be implemented in the subclass.'
		)

