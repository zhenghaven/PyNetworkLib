#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import threading

from ...Utils.HandlerState import HandlerState
from ..DownstreamHandlerBase import DownstreamHandlerBase
from ..Utils.HostField import HOST_FIELD_TYPES
from ..PreHandler import PreHandler
from .Types import HANDLER_FUNCTION_TYPE


class HandlerByPath(DownstreamHandlerBase):
	'''A handler that routes requests to different handlers based on the path.'''

	def __init__(
		self,
		handlerFunc: HANDLER_FUNCTION_TYPE,
	) -> None:
		'''
		Constructor for the HandlerByPath class.
		'''

		super().__init__()
		self._handlerFunc = handlerFunc

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

		# Call the handler function
		self._handlerFunc(
			host=host,
			relPath=relPath,
			pyHandler=pyHandler,
			handlerState=handlerState,
			reqState=reqState,
			terminateEvent=terminateEvent,
		)

