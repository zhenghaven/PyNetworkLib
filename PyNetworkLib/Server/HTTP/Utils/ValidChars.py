#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###



VALID_CHARS_ALPHA_LOWER = 'abcdefghijklmnopqrstuvwxyz'
VALID_CHARS_ALPHA_UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
VALID_CHARS_NUM         = '0123456789'
VALID_CHARS_SAFE_SAFE   = '-_'
VALID_CHARS_SAFE        = VALID_CHARS_SAFE_SAFE + '$.+!*\'(),'
VALID_CHARS_RESERVED    = ';/?:@=&'


VALID_CHARS_PATH = VALID_CHARS_ALPHA_LOWER + \
	VALID_CHARS_ALPHA_UPPER + \
	VALID_CHARS_NUM + \
	VALID_CHARS_SAFE_SAFE


VALID_CHARS_PATH_QUERY = VALID_CHARS_PATH + \
	VALID_CHARS_SAFE + \
	VALID_CHARS_RESERVED


VALID_CHARS_PATH_SET = set(VALID_CHARS_PATH)
VALID_CHARS_PATH_QUERY_SET = set(VALID_CHARS_PATH_QUERY)

