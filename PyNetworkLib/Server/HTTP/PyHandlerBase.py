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

	def AddHeader(self, key: str, value: str) -> None:
		'''
		Set the header for the response.
		'''
		if not hasattr(self, '_headers'):
			self._headers = {}

		if key not in self._headers:
			self._headers[key] = []
		self._headers[key].append(value)

	def SetBody(self, body: bytes) -> None:
		'''
		Set the body for the response.
		'''
		self._body = body

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
		if not hasattr(self, '_body'):
			self._body = None

		return self._body

	@property
	def headerItems(self):
		'''
		Get the header.items() for the response.
		'''
		if not hasattr(self, '_headers'):
			self._headers = {}

		return self._headers.items()

	def GetHeader(self, key: str) -> list[str] | None:
		'''
		Get the header for the response.
		'''
		if not hasattr(self, '_headers'):
			self._headers = {}

		res = self._headers.get(key, None)
		return res.copy() if res is not None else None

	def SetHeader(self, key: str, values: list[str]) -> None:
		'''
		Update the header for the response.
		'''
		if not hasattr(self, '_headers'):
			self._headers = {}

		self._headers[key] = values.copy()

	def ResetHeaders(self) -> None:
		'''
		Reset the headers for the response.
		'''
		if not hasattr(self, '_headers'):
			self._headers = {}

		self._headers.clear()

	def ResetBody(self) -> None:
		'''
		Reset the body for the response.
		'''
		self._body = None

	def Reset(self) -> None:
		'''
		Reset the response.
		'''
		self.ResetHeaders()
		self.ResetBody()
		self.SetStatusCode(500)

	def SetJSONBodyFromDict(
		self,
		data: dict,
		indent: int | str | None = None,
		statusCode: int | None = None,
	) -> None:
		'''
		Set the body for the response as a JSON string.
		'''
		self.SetBody(json.dumps(data, indent=indent).encode('utf-8'))
		self.AddHeader('Content-Type', 'application/json')
		self.AddHeader('Content-Length', str(len(self._body)))

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

		self.SetBody(message.encode('utf-8', 'replace'))
		self.AddHeader('Content-Length', str(len(self._body)))
		self.AddHeader('Content-Type', 'text/plain')

	def DoResponse(self) -> None:
		'''
		Send the response to the client.
		'''
		self.log_request(
			code=self.statusCode,
			size=len(self.body) if self.body is not None else 0,
		)

		# set the response code
		self.send_response_only(self.statusCode)

		# set the headers
		for key, values in self.headerItems:
			for value in values:
				self.send_header(key, value)
		self.end_headers()

		# set the body
		if self.body is not None:
			self.wfile.write(self.body)

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

