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


class HandlerState:
	'''Handler state class.

	This class is used to store the state of the handler.
	'''

	def __init__(self):
		'''
		Constructor for the handler state class.
		'''

		self._lock = threading.Lock()
		self._store: dict[str, Any] = {}

		self._logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')
		self._logger.debug('Handler state initialized.')

	def __getitem__(self, key: str) -> Any:
		'''
		Get the value of the specified key.

		:param key: The key to get.
		'''
		with self._lock:
			return self._store[key]

		self._logger.debug('Handler state key %s retrieved.', key)

	def __setitem__(self, key: str, value: Any) -> None:
		'''
		Set the value of the specified key.

		:param key: The key to set.
		:param value: The value to set.
		'''
		with self._lock:
			self._store[key] = value

		self._logger.info('Handler state key %s created.', key)

