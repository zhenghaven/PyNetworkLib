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
from ..Utils.HostField import HOST_FIELD_TYPES
from ..Utils.ValidChars import VALID_CHARS_PATH
from ..PyHandlerBase import PyHandlerBase
from .Types import HANDLER_FUNCTION_TYPE, PATH_MAP_TYPE


class InvalidPathError(ValueError):
	'''
	A custom error class to raise when the path is invalid.
	'''

	def __init__(self, path: str) -> None:
		super().__init__(f'Invalid path: {path}. The path must start with a "/".')
		self.path = path


def _IdxOfNextSplitPoint(path: str, startIdx: int) -> int:
	'''
	A function to find the index of the next split point in the path.
	The split point is defined as the first character that is not in
	the VALID_CHARS_PATH set.
	'''
	for idx in range(startIdx, len(path)):
		if path[idx] not in VALID_CHARS_PATH:
			return idx

	# if no split point is found, return the length of the path, which is
	# one past the end of the path
	return len(path)


def _SplitThisAndNextLevelPath(path: str) -> tuple[str, str]:
	if path == '':
		# empty path itself is a valid path but it does not have a next level
		return '', ''
	if path[0] == '/':
		# the path must start with a '/'
		endIdx = _IdxOfNextSplitPoint(path, 1)
		thisLevelPath = path[:endIdx]
		nextLevelPath = path[endIdx:]
		return thisLevelPath, nextLevelPath
	# if the path does not start with a '/', it is not a valid path
	raise InvalidPathError(path)


def HandlerByPathMap(pathMap: PATH_MAP_TYPE) -> HANDLER_FUNCTION_TYPE:
	'''
	A function to transform a dictionary of path to handler functions into
	a handler function that can be called by the upstream handler.
	'''
	def HandlerByPathInner(
		host: HOST_FIELD_TYPES,
		relPath: str,
		pyHandler: PyHandlerBase,
		handlerState: HandlerState,
		reqState: dict,
		terminateEvent: threading.Event,
	) -> None:
		'''
		The inner handler function that is called by the upstream handler.
		It will call the appropriate handler function based on the path
		and method of the request.
		'''

		method = pyHandler.command

		try:
			thisLevelPath, nextLevelPath = _SplitThisAndNextLevelPath(relPath)
		except InvalidPathError as e:
			# if the path is not valid, return a 404 error
			pyHandler.SetCodeAndTextMessage(404, 'Not Found')
			return

		methodHdlrMap = pathMap.get(thisLevelPath, None)
		if methodHdlrMap is None:
			# if the path is not found, return a 404 error
			pyHandler.SetCodeAndTextMessage(404, 'Not Found')
			return

		# if the path is found, check if the method is valid
		handler = methodHdlrMap.get(method, None)
		if handler is None:
			# if the method is not found, return a 404 error
			pyHandler.SetCodeAndTextMessage(404, 'Not Found')
			return

		# call the handler function
		handler(
			host=host,
			relPath=nextLevelPath,
			pyHandler=pyHandler,
			handlerState=handlerState,
			reqState=reqState,
			terminateEvent=terminateEvent,
		)

	return HandlerByPathInner


def EndPointHandler(handler: HANDLER_FUNCTION_TYPE) -> HANDLER_FUNCTION_TYPE:
	'''
	A decorator to create and handler function that should be the end of a path,
	meaning that the `relPath` should be empty or a query string.
	'''
	def EndPointHandlerInner(
		host: HOST_FIELD_TYPES,
		relPath: str,
		pyHandler: PyHandlerBase,
		handlerState: HandlerState,
		reqState: dict,
		terminateEvent: threading.Event,
	) -> None:
		if relPath == '':
			handler(
				host=host,
				relPath=relPath,
				pyHandler=pyHandler,
				handlerState=handlerState,
				reqState=reqState,
				terminateEvent=terminateEvent,
			)
			return

		# if the `relPath` is not empty, return a 404 error
		pyHandler.SetCodeAndTextMessage(404, 'Not Found')

	return EndPointHandlerInner

