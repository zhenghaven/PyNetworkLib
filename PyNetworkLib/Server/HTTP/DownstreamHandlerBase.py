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
from .Utils.HostField import HOST_FIELD_TYPES


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
		*, # required that all parameters are keyword-only
		host: HOST_FIELD_TYPES,
		relPath: str,
		pyHandler: PyHandlerBase,
		handlerState: HandlerState,
		reqState: dict,
		terminateEvent: threading.Event,
	) -> None:
		'''Handle the request.

		:param relPath: The relative path (without the domain/host name part)
		of the request.
		:param host: The host field parsed from the request header.
		:param pyHandler: The HTTP request handler object.
		:param handlerState: The state of the handler of a server shared by
			all requests made to that server.
		:param reqState: The state of the current request.
		:param terminateEvent: The event that is set when the server is
			terminated.
		'''

		raise NotImplementedError(
			'Handle() method must be implemented in the subclass.'
		)

