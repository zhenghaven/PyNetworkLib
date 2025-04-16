#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import http.server
import json


class PyHandlerBase(http.server.BaseHTTPRequestHandler):

	def AddResponseHeader(self, key: str, value: str) -> None:
		'''
		Set the header for the response.
		'''
		if not hasattr(self, '_respHeaders'):
			self._respHeaders = {}

		if key not in self._respHeaders:
			self._respHeaders[key] = []
		self._respHeaders[key].append(value)

	def SetResponseBody(self, body: bytes) -> None:
		'''
		Set the body for the response.
		'''
		self._respBody = body

	def SetStatusCode(self, code: int) -> None:
		'''
		Set the status code for the response.
		'''
		self._statusCode = code

	@property
	def hasResponseSent(self) -> bool:
		'''
		Check if the response has been sent.
		'''
		if not hasattr(self, '_wasResponseSent'):
			self._wasResponseSent = False

		return self._wasResponseSent

	@property
	def statusCode(self) -> int:
		'''
		Get the status code for the response.
		'''
		if not hasattr(self, '_statusCode'):
			self._statusCode = 500

		return self._statusCode

	@property
	def body(self) -> bytes | None:
		'''
		Get the body for the response.
		'''
		if not hasattr(self, '_respBody'):
			self._respBody = None

		return self._respBody

	@property
	def respHeaderItems(self):
		'''
		Get the header.items() for the response.
		'''
		if not hasattr(self, '_respHeaders'):
			self._respHeaders = {}

		return self._respHeaders.items()

	def GetResponseHeader(self, key: str) -> list[str] | None:
		'''
		Get the header for the response.
		'''
		if not hasattr(self, '_respHeaders'):
			self._respHeaders = {}

		res = self._respHeaders.get(key, None)
		return res.copy() if res is not None else None

	def SetResponseHeader(self, key: str, values: list[str]) -> None:
		'''
		Update the header for the response.
		'''
		if not hasattr(self, '_respHeaders'):
			self._respHeaders = {}

		self._respHeaders[key] = values.copy()

	def ResetResponseHeaders(self) -> None:
		'''
		Reset the headers for the response.
		'''
		if not hasattr(self, '_respHeaders'):
			self._respHeaders = {}

		self._respHeaders.clear()

	def ResetResponseBody(self) -> None:
		'''
		Reset the body for the response.
		'''
		self._respBody = None

	def ResetResponse(self) -> None:
		'''
		Reset the response.
		'''
		self.ResetResponseHeaders()
		self.ResetResponseBody()
		self.SetStatusCode(500)
		self._wasResponseSent = False

	def SetJSONBodyFromDict(
		self,
		data: dict,
		indent: int | str | None = None,
		statusCode: int | None = None,
	) -> None:
		'''
		Set the body for the response as a JSON string.
		'''
		self.SetResponseBody(json.dumps(data, indent=indent).encode('utf-8'))
		self.AddResponseHeader('Content-Type', 'application/json')
		self.AddResponseHeader('Content-Length', str(len(self._respBody)))

		if statusCode is not None:
			self.SetStatusCode(statusCode)

	def SetCodeAndTextMessage(
		self,
		code: int,
		message: str,
	) -> None:
		'''
		Set the status code and message for the response.
		'''
		self.SetStatusCode(code)

		self.SetResponseBody(message.encode('utf-8', 'replace'))
		self.AddResponseHeader('Content-Length', str(len(self._respBody)))
		self.AddResponseHeader('Content-Type', 'text/plain')

	def DoResponse(self) -> None:
		'''
		Send the response to the client.
		'''
		self.log_request(
			code=self.statusCode,
			size=len(self._respBody) if self._respBody is not None else 0,
		)

		# send the response code
		self.send_response_only(self.statusCode)

		# send the headers
		for key, values in self.respHeaderItems:
			for value in values:
				self.send_header(key, value)
		self.end_headers()

		# send the body
		if self._respBody is not None:
			self.wfile.write(self._respBody)
			# self.wfile.flush()

		self._wasResponseSent = True

	def SetRequestQuery(self, query: str) -> None:
		'''
		Set the request query string that was received in request.
		'''
		self._requestQuery = query

	def GetRequestQuery(self) -> str:
		'''
		Get the request query string that was received in request.
		'''
		if not hasattr(self, '_requestQuery'):
			self._requestQuery = ''

		return self._requestQuery

	def GetRequestKeepAlive(self) -> bool:
		'''
		Get the request keep-alive value from the request header.
		'''
		keepAlive = self.headers.get('Connection', None)
		if (keepAlive is None) or (not isinstance(keepAlive, str)):
			# the header is not set or not a string
			return False

		keepAlive = keepAlive.lower()
		if keepAlive == 'keep-alive':
			return True

		# all other values are not keep-alive (i.e., close)
		return False

	def AllowKeepAlive(self) -> None:
		'''Allow to keep the connection alive if keep-alive is requested.'''
		if self.GetRequestKeepAlive():
			self.AddResponseHeader('Connection', 'keep-alive')

