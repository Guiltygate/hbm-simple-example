'''
Basic utilities for python scripts.

Author: Eric Ames
Creation Date: 2015-11-05
'''

import re
from os import path


def strs( pattern ,string):
	a = re.search( pattern ,string)
	if not a:
		return False
	else:
		return a.group(0)


def convert( base ,target):
	if isinstance( base ,target):
		return base
	elif isinstance( base ,str):
		if target == bool:
			if base == '0' or strs( '[Ff]alse' ,base)\
						or strs( '^[Nn]' ,base):
				return False
			else:
				return bool(base)
		elif target == int:
			try:
				return int(base)
			except ValueError:
				print( "Tried to convert string to int.")
		
	elif isinstance( base ,int) or isinstance( base ,float):
		if target == bool:
			return bool( base)
		elif target == str:
			return str( base)

	elif isinstance( base ,bool):
		if target == str:
			return str( base)
		elif target == int:
			return int( base)


def depthPrint( t ,tab):
	if not tab:
		tab = ""
	for v in t:
		print( tab+v)
		if type(v) == 'list':
			depthPrint( v ,'\t')