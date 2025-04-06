#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###

# The original implementation of socketserver suffers from the race condition
# issue when one thread is trying to start the server while another thread is
# trying to stop the server.
# The replacement implementation here is based on the original implementation
# with the necessary mitigation


import ipaddress
import logging
import selectors
import socket
import socketserver
import threading

from .ServerBase import ServerBase


_LOGGER = logging.getLogger(__name__)


# poll/select have the advantage of not requiring any extra file descriptor,
# contrarily to epoll/kqueue (also, they require a single syscall).
if hasattr(selectors, 'PollSelector'):
	_ServerSelector = selectors.PollSelector
else:
	_ServerSelector = selectors.SelectSelector


def _GetIpAddrVer(ipAddr: str) -> int | None:
	try:
		ip = ipaddress.ip_address(ipAddr)
		return ip.version
	except:
		# the given string is not a valid IP address
		return None


def _FixAddrFamily(
	oriCls: type[socketserver.BaseServer],
	obj: socketserver.BaseServer,
	args: list,
	kwargs: dict,
) -> None:
	if not hasattr(obj, 'address_family'):
		# the address family was not set in the original object
		# so we ignore it
		return

	if (
		getattr(obj, 'address_family') != socket.AF_INET
		and getattr(obj, 'address_family') != socket.AF_INET6
	):
		# the instance is not about IPv4 or IPv6
		# so we ignore it
		return

	serverAddr = None
	if 'server_address' in kwargs:
		# the server address was set in the kwargs
		serverAddr = kwargs['server_address']
	elif len(args) > 0:
		# there are positional arguments
		possibleAddr = args[0]
		if (
			hasattr(possibleAddr, '__len__')
			and hasattr(possibleAddr, '__getitem__')
		):
			# the first argument has a length and is indexable
			if (
				len(possibleAddr) >= 2
				and isinstance(possibleAddr[0], str)
				and isinstance(possibleAddr[1], int)
			):
				# the first argument satisfies the format of (str, int, ...)
				serverAddr = possibleAddr

	if serverAddr is None:
		# we can't find the server address from the arguments
		# so we ignore it
		return

	ipVer = _GetIpAddrVer(serverAddr[0])
	if (ipVer == 4) and (getattr(obj, 'address_family') != socket.AF_INET):
		# a fix is needed
		_LOGGER.debug('Fixing address family from IPv6 to IPv4')
		setattr(obj, 'address_family', socket.AF_INET)
	elif (ipVer == 6) and (getattr(obj, 'address_family') != socket.AF_INET6):
		# a fix is needed
		_LOGGER.debug('Fixing address family from IPv4 to IPv6')
		setattr(obj, 'address_family', socket.AF_INET6)
	# if ipVer is None, we don't change the address family
	# since it could be a domain name or something else
	# and in such a case, the caller is responsible for making sure
	# that the address family is correct


def MitigateServeAndShutdown(oriCls: socketserver.BaseServer) -> type[socketserver.BaseServer]:

	class _MitigatedServer(oriCls):

		def __init__(self, *args, **kwargs):

			_FixAddrFamily(oriCls, self, args, kwargs)

			super().__init__(*args, **kwargs)
			self.__hasShutdownRequest = threading.Event()

		def serve_forever(self, poll_interval=0.5):

			with _ServerSelector() as selector:
				selector.register(self, selectors.EVENT_READ)

				while not self.__hasShutdownRequest.is_set():
					ready = selector.select(poll_interval)
					if self.__hasShutdownRequest.is_set():
						break
					if ready:
						self._handle_request_noblock()

					self.service_actions()

		def shutdown(self):
			self.__hasShutdownRequest.set()

	return _MitigatedServer


def FromPySocketServer(oriCls: type[socketserver.BaseServer]) -> type[ServerBase]:

	_MitigatedCls: type[socketserver.BaseServer] = MitigateServeAndShutdown(oriCls)

	class _PySocketServerAndServer(_MitigatedCls, ServerBase):

		def __init__(
			self,
			*args,
			serverInit: dict[str, any] | None = {},
			**kwargs,
		) -> None:
			# calls the __init__ of the MitigatedCls first due to the MRO
			super().__init__(*args, **kwargs)

			# calls the __init__ of the class after the MitigatedCls (i.e., ServerBase)
			ServerBase.__init__(self)

			if serverInit is not None:
				self.ServerInit(**serverInit)

		def _ServeForever(self) -> None:
			self.serve_forever()

		def _Shutdown(self) -> None:
			self.shutdown()

		def _CleanUp(self) -> None:
			self.server_close()

		def GetSrcPort(self) -> int:
			return self.server_address[1]

	return _PySocketServerAndServer

