#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import unittest

from PyNetworkLib.Server.Utils.HandlerState import HandlerState


class TestHandlerState(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_Server_HTTP_Utils_HandlerState_01CreateState(self):
		state = HandlerState()
		self.assertIsInstance(state, HandlerState)

	def test_Server_HTTP_Utils_HandlerState_02SetState(self):
		state = HandlerState()

		testObj1 = { 'key': 'value' }
		testObj2 = { 'key': 'value2' }
		testObj3 = { 'key': 'value3' }

		# create a new state
		state['key1'] = testObj1
		self.assertEqual(state._store['key1'], testObj1)
		self.assertNotEqual(state._store['key1'], testObj2)

		# create another state
		state['key2'] = testObj2
		self.assertEqual(state._store['key2'], testObj2)
		self.assertNotEqual(state._store['key2'], testObj1)
		self.assertNotEqual(state._store['key1'], state._store['key2'])

		# overwrite the first state
		state['key1'] = testObj3
		self.assertEqual(state._store['key1'], testObj3)
		self.assertNotEqual(state._store['key1'], testObj1)
		self.assertNotEqual(state._store['key1'], testObj2)
		self.assertNotEqual(state._store['key1'], state._store['key2'])
		self.assertEqual(state._store['key2'], testObj2)
		self.assertNotEqual(state._store['key2'], testObj3)
		self.assertNotEqual(state._store['key2'], testObj1)
		self.assertNotEqual(state._store['key2'], state._store['key1'])

	def test_Server_HTTP_Utils_HandlerState_03GetState(self):
		state = HandlerState()

		testObj1 = { 'key': 'value' }
		state['key1'] = testObj1
		testObj2 = { 'key': 'value2' }
		state['key2'] = testObj2

		# get the first state
		self.assertEqual(state['key1'], testObj1)
		self.assertNotEqual(state['key1'], testObj2)

		# get the second state
		self.assertEqual(state['key2'], testObj2)
		self.assertNotEqual(state['key2'], testObj1)

