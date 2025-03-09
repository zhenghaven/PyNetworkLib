#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import sys
import unittest


from . import TestModules


def main() -> None:
	unittest.main(
		module=TestModules,
		argv=[ sys.argv[0], '-v', ],
	)

