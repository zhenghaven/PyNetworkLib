#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


from .PyHandlerBase import PyHandlerBase
from .ServerBase import ServerBase


class PreHandler(PyHandlerBase):
	disable_nagle_algorithm = True

	server: ServerBase

	def setup(self) -> None:
		super().setup()

		self.cltAddrStr = f'{self.client_address[0]}:{self.client_address[1]}'
		self.server.handlerLogger.debug(f'Setting up handler for {self.cltAddrStr}')

	def handle(self):
		# get ip address of the client
		clientIP = str(self.client_address[0])
		clientPort = int(self.client_address[1])

		try:
			reqState = {
				'clientIP': clientIP,
				'clientPort': clientPort,
			}
			self.server.downstreamTCPHdlr.HandleRequest(
				pyHandler=self,
				handlerState=self.server.handlerState,
				reqState=reqState,
				terminateEvent=self.server.terminateEvent,
			)
		except Exception as e:
			self.server.handlerLogger.debug(
				f'Handler for {self.cltAddrStr} failed with error: {e}'
			)
			pass

	def finish(self) -> None:
		self.server.handlerLogger.debug(f'Finishing {self.cltAddrStr} handler')
		super().finish()

