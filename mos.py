'''
	Author: Eric Ames
	Date: 2016-03-10
	General purpose functions for OS/terminal commands.
'''

import os
import sys
from misc import strs

OS = sys.platform
stateDIR = os.path.expanduser('~')
pgPass = os.path.expanduser('~')
if OS == 'win32':
	stateDIR = stateDIR + '\\Saved_States'
	pgPass = pgPass + '\\AppData\\Roaming\\postgresql\\pgpass.conf'
else:
	stateDIR = stateDIR + '/Saved_States'
	pgPass = pgPass + '/.pgpass'



def cmd( c):
	r = os.popen( c).read()
	if r == "":
		return False
	else:
		return r

def cmdS( c):
	os.system( c)

def clear():
	if OS == 'win32':
		cmdS( 'cls')
	else:
		cmdS('clear')

def setupDir():
	if not os.path.exists( stateDIR):
		cmd( 'mkdir ' + stateDIR)

def setPermission( num ,fn):
	if OS != 'win32':
		cmd( 'chmod ' + num + ' ' + fn)


def getDirContents( ext='.*'):
	d = os.listdir( stateDIR)
	if ext:
		l = []
		for v in d:
			if strs( ext ,v):
				l.append( v)
		return l
	else:
		return d

def reset():
	cmd( 'reset')

def exit():
	sys.exit(0)