#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import logging
import threading

from typing import Any


class ServerBase:

	def ServerInit(
		self,
		addData: dict[str, Any] = {},
	) -> None:

		self.terminateEvent = threading.Event()

		self.stateLock = threading.Lock()
		self.hasServeThreadStarted = False

		self._clsName = f'{__name__}.{self.__class__.__name__}'
		self._logger = logging.getLogger(self._clsName)

		self.handlerName = self.RequestHandlerClass.__name__
		self.handlerLoggerName = f'{self._clsName}.{self.handlerName}'
		self.handlerLogger = logging.getLogger(self.handlerLoggerName)

		for addDataKey, addDataVal in addData.items():
			setattr(self, addDataKey, addDataVal)

	def _ServeForever(self) -> None:
		raise NotImplemented(
			f'{self.__class__.__name__}._ServeForever() is not implemented'
		)

	def ServeUntilTerminate(self) -> None:
		self._logger.info('Server started to serve')
		self._ServeForever()

	def ThreadedServeUntilTerminate(self) -> None:
		with self.stateLock:
			if self.hasServeThreadStarted:
				# the `ThreadedServeUntilTerminate` method has already started
				# the serve thread, so we should not start another one
				return

			if self.terminateEvent.is_set():
				# the `Terminate` method has already been called
				# so we should not start the serve thread
				return

			# otherwise, the `Terminate` method has not entered the
			# `with self.stateLock:` critical section,
			# so it is safe to start the thread

			self.hasServeThreadStarted = True

			self._logger.info('Creating serve thread...')
			self._serveThread = threading.Thread(
				target=self.ServeUntilTerminate,
			)
			self._logger.debug('Starting serve thread...')
			self._serveThread.start()

	def _Shutdown(self) -> None:
		raise NotImplemented(
			f'{self.__class__.__name__}._Shutdown() is not implemented'
		)

	def _CleanUp(self) -> None:
		raise NotImplemented(
			f'{self.__class__.__name__}._CleanUp() is not implemented'
		)

	def Terminate(self) -> None:
		self.terminateEvent.set()

		self._Shutdown()

		with self.stateLock:
			if self.hasServeThreadStarted:
				# the `ThreadedServeUntilTerminate` method has started the serve
				# thread, so we should wait for it to complete
				self._serveThread.join()

		self._CleanUp()

	def GetSrcPort(self) -> int:
		raise NotImplemented(
			f'{self.__class__.__name__}.GetSrcPort() is not implemented'
		)

