#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import argparse


def GetPackageInfo() -> dict:
	import os

	thisDir = os.path.dirname(os.path.abspath(__file__))
	possibleRepoDir = os.path.dirname(thisDir)
	possibleTomlPath = os.path.join(possibleRepoDir, 'pyproject.toml')

	pkgInfo = {
		'name': __package__ or __name__,
	}

	if os.path.exists(possibleTomlPath):
		import tomllib
		with open(possibleTomlPath, 'rb') as file:
			tomlData = tomllib.load(file)
		if (
			('project' in tomlData) and
			('name' in tomlData['project']) and
			(tomlData['project']['name'] == pkgInfo['name'])
		):
			pkgInfo['description'] = tomlData['project']['description']
			pkgInfo['version'] = tomlData['project']['version']
			return pkgInfo

	import importlib
	pkgInfo['version'] = importlib.metadata.version(pkgInfo['name'])
	pkgInfo['description'] = importlib.metadata.metadata(pkgInfo['name'])['Summary']
	return pkgInfo



def main() -> None:
	pkgInfo = GetPackageInfo()

	argParser = argparse.ArgumentParser(
		description=pkgInfo['description'],
		prog='',
	)
	argParser.add_argument(
		'--version',
		action='version', version=pkgInfo['version'],
	)
	args = argParser.parse_args()

	# this is a library package
	# there is no functionality to run other than displaying the version
	# so print usage and exit with code 1
	argParser.exit(1, argParser.format_usage())


if __name__ == '__main__':
	main()

