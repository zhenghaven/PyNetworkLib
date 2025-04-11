#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import socket
import ssl

from typing import Any, overload

from ...TLS.SSLContext import SSLContext


class ListenSocket:
	'''
	The class that wraps the ssl.SSLSocket class to provide better support for
	the listening socket on the server side.
	'''

	def __init__(
		self,
		sock: socket.socket,
		sslContext: SSLContext,
	) -> None:

		self._sock = sock
		self._sslContext = sslContext

	def accept(self) -> tuple[ssl.SSLSocket, tuple[str, int]]:
		'''
		Accepts a connection on the socket and returns a tuple of the
		accepted socket and the address of the remote peer.

		NOTE: this is where the "magic" happens.
		'''

		sock, addr = self._sock.accept()

		self._sslContext.ReloadCertChainFilesIfExpired()
		sock = self._sslContext.WrapSocket(
			sock=sock,
			server_side=True,
			do_handshake_on_connect=True,
		)
		return sock, addr

	def bind(self, address: tuple[str, int]) -> None:
		'''
		Binds the socket to the address.
		'''
		self._sock.bind(address)

	def close(self) -> None:
		'''
		Closes the socket.
		'''
		self._sock.close()

	def connect(self, address: tuple[str, int]) -> None:
		'''
		Connects the socket to the address.
		'''
		raise RuntimeError(
			'A server listening socket should not be used to connect to a remote address.'
		)

	def connext_ex(self, address: tuple[str, int]) -> None:
		'''
		Connects the socket to the address.
		'''
		raise RuntimeError(
			'A server listening socket should not be used to connect to a remote address.'
		)

	def detach(self) -> None:
		'''
		Detaches the socket
		'''
		self._sock.detach()

	def fileno(self) -> int:
		'''
		Returns the file descriptor of the socket.
		'''
		return self._sock.fileno()

	def getpeername(self) -> tuple[str, int]:
		'''
		Returns the address of the remote peer.
		'''
		return self._sock.getpeername()

	def getsockname(self) -> tuple[str, int]:
		'''
		Returns the address of the local socket.
		'''
		return self._sock.getsockname()

	@overload
	def getsockopt(self, level: int, optname: int) -> int:
		'''
		Gets the socket option.
		'''
		return self._sock.getsockopt(level, optname)

	@overload
	def getsockopt(self, level: int, optname: int, buflen: int) -> bytes:
		'''
		Gets the socket option.
		'''
		return self._sock.getsockopt(level, optname, buflen)

	def getblocking(self) -> bool:
		'''
		whether the socket is blocking or not.
		'''
		return self._sock.getblocking()

	def gettimeout(self) -> float | None:
		'''
		Gets the timeout of the socket.
		'''
		return self._sock.gettimeout()

	def listen(self, backlog: int=...) -> None:
		'''
		Listens for incoming connections.
		'''
		self._sock.listen(backlog)

	def makefile(
		self,
		mode: str='r',
		buffering: int | None=None,
		*,
		encoding: str | None=None,
		errors: str | None=None,
		newline: str | None=None,
	):
		'''
		Makes a file object from the socket.
		'''
		return self._sock.makefile(
			mode,
			buffering,
			encoding=encoding,
			errors=errors,
			newline=newline,
		)

	def recv(self, bufsize: int, flags: int=...) -> bytes:
		'''
		Receives data from the socket.
		'''
		# self._sock.recv(bufsize, flags)
		raise RuntimeError(
			'A server listening socket should not be used to receive data'
		)

	def recvfrom(self, bufsize: int, flags: int=...) -> tuple[bytes, tuple[str, int]]:
		'''
		Receives data from the socket.
		'''
		# self._sock.recvfrom(bufsize, flags)
		raise RuntimeError(
			'A server listening socket should not be used to receive data'
		)

	def recvmsg(
		self,
		bufsize: int,
		ancbufsize: int = ...,
		flags: int = ...,
	) -> tuple[bytes, list[tuple[int, int, bytes]], int, Any]:
		'''
		Receives data from the socket.
		'''
		# self._sock.recvmsg(bufsize, ancbufsize, flags)
		raise RuntimeError(
			'A server listening socket should not be used to receive data'
		)

	def recvmsg_into(
		self,
		buffers: bytearray,
		ancbufsize: int = ...,
		flags: int = ...,
	) -> tuple[int, list[tuple[int, int, bytes]], int, Any]:
		'''
		Receives data from the socket.
		'''
		# self._sock.recvmsg_into(buffers, ancbufsize, flags)
		raise RuntimeError(
			'A server listening socket should not be used to receive data'
		)

	def recvfrom_into(
		self,
		buffer: bytearray,
		nbytes: int = ...,
		flags: int = ...,
	) -> tuple[int, tuple[str, int]]:
		'''
		Receives data from the socket.
		'''
		# self._sock.recvfrom_into(buffer, nbytes, flags)
		raise RuntimeError(
			'A server listening socket should not be used to receive data'
		)

	def recv_into(
		self,
		buffer: bytearray,
		nbytes: int = ...,
		flags: int = ...,
	) -> int:
		'''
		Receives data from the socket.
		'''
		# self._sock.recv_into(buffer, nbytes, flags)
		raise RuntimeError(
			'A server listening socket should not be used to receive data'
		)

	def send(self, data: bytes, flags: int=...) -> int:
		'''
		Sends data to the socket.
		'''
		# self._sock.send(data, flags)
		raise RuntimeError(
			'A server listening socket should not be used to send data'
		)

	def sendall(self, data: bytes, flags: int=...) -> None:
		'''
		Sends data to the socket.
		'''
		# self._sock.sendall(data, flags)
		raise RuntimeError(
			'A server listening socket should not be used to send data'
		)

	@overload
	def sendto(
		self,
		data: bytes,
		flags: int,
		address: tuple[str, int],
	) -> int:
		'''
		Sends data to the socket.
		'''
		# self._sock.sendto(data, flags, address)
		raise RuntimeError(
			'A server listening socket should not be used to send data'
		)

	@overload
	def sendto(
		self,
		data: bytes,
		address: tuple[str, int],
	) -> int:
		'''
		Sends data to the socket.
		'''
		# self._sock.sendto(data, address)
		raise RuntimeError(
			'A server listening socket should not be used to send data'
		)

	def sendmsg(
		self,
		buffers,
		ancdata = ...,
		flags: int = ...,
		address: tuple[str, int] | None = ...,
	) -> int:
		'''
		Sends data to the socket.
		'''
		# self._sock.sendmsg(buffers, ancdata, flags, address)
		raise RuntimeError(
			'A server listening socket should not be used to send data'
		)

	def setblocking(self, flag: bool) -> None:
		'''
		Sets the blocking mode of the socket.
		'''
		self._sock.setblocking(flag)

	def settimeout(self, value: float | None) -> None:
		'''
		Sets the timeout of the socket.
		'''
		self._sock.settimeout(value)

	@overload
	def setsockopt(
		self,
		level: int,
		optname: int,
		value: Any,
	) -> None:
		'''
		Sets the socket option.
		'''
		self._sock.setsockopt(level, optname, value)

	@overload
	def setsockopt(
		self,
		level: int,
		optname: int,
		value: None,
		optlen: int,
	) -> None:
		'''
		Sets the socket option.
		'''
		self._sock.setsockopt(level, optname, value, optlen)

	def shutdown(self, how: int) -> None:
		'''
		Shuts down the socket.
		'''
		self._sock.shutdown(how)

	@property
	def family(self) -> socket.AddressFamily:
		'''
		Returns the address family of the socket.
		'''
		return self._sock.family

	@property
	def type(self) -> socket.SocketKind:
		'''
		Returns the socket type of the socket.
		'''
		return self._sock.type

	@property
	def proto(self) -> int:
		'''
		Returns the protocol of the socket.
		'''
		return self._sock.proto

