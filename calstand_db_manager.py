'''
	Author: Eric Ames
	Date: 2016-03-08
	Command-line psql db manager.
	Facilitates custom queries on calibration_instruments table, along with
	cluster save/load features for recovery.
'''


import mos
import ui as screen
from instrument_manager import instrumentMenu ,reloadConnConfig
from state_manager import stateMenu ,viewConnStatus ,changeConnConfig


def changeConnStatus():
	changeConnConfig()
	reloadConnConfig()

def mainMenu():
	main = [
		["HBM CalStand Database Manager" ,None]
 		,['Update CalStand instruments' ,instrumentMenu]
 		,['Save/Load CalStand Database' ,stateMenu]
 		,['View Connection Setup' ,viewConnStatus]
 		,['Change Connection Setup' ,changeConnStatus]]
	screen.menuSelection( main)


mos.setupDir()

screen.show( '''
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\//////////////////////
Welcome to the HBM CalStand Database Manager!
//////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
''' ,True)

screen.get( 'If PCE is closed, please press ENTER.')

mainMenu()

mos.exit()



