#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import threading

from typing import Callable

from ...Utils.HandlerState import HandlerState
from ..Utils.HostField import HOST_FIELD_TYPES
from ..PyHandlerBase import PyHandlerBase


HANDLER_FUNCTION_TYPE = Callable[
	[
		HOST_FIELD_TYPES,
		str,
		PyHandlerBase,
		HandlerState,
		dict,
		threading.Event,
	],
	None,
]


METHOD_TYPE = str
PATH_TYPE = str


PATH_MAP_TYPE = dict[
	PATH_TYPE,
	dict[METHOD_TYPE, HANDLER_FUNCTION_TYPE],
]

