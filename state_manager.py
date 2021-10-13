
'''
db-state manager
'''

from psql import psqlConn
import ui as screen
from misc import strs
import mos

dbConn = psqlConn()


def stateMenu():
	constructor = [
		 ['DB State Menu' ,None]
		,['Manage DB State' ,manageDBState]
		,['Load Calibration File' ,[fileSelection ,[__loadState ,'.cal']]]
		,[ 'Reset DB State to Factory' ,resetDB]]
	screen.menuSelection( constructor)

def manageDBState():
	if dbConn.isTriptych():
		screen.show( 'Your host database is one of the Triptych servers.\
		\nYou are not allowed to make database state changes.' ,prompt=True)
		return
	cont = [
		 ['DB State Menu' ,None]
		,['Save DB State' ,saveState]
		,['Load DB State' ,[fileSelection ,[__loadState ,None]]]]
	screen.menuSelection( cont)


def viewConnStatus():
	view = '''CalStand Manager Connection Setup
------------------------------
Station: ''' + dbConn.stationName + '\nHost: ' + dbConn.args['host']
	screen.show( view ,True ,prompt=True)

def changeConnConfig():
	dbConn.configSetup()


def saveState():
	while True:
		fileName = screen.get( 'Enter name for file (q to quit): ' ,str ,30 ,'.*' ,'    ')
		if fileName[0] == 'q': return

		if not strs( '.pgd' ,fileName):
			fileName = fileName + '.pgd'

		if __fileNameExists( fileName):
			if screen.confirm( 'File already exists. Overwrite?'):
				break
		else:
			break
	__defaultDlg( dbConn.pgDump ,mos.stateDIR + '/' + fileName)

def fileSelection( t):
	fn ,ext = t[0] ,t[1]
	if ext == '.cal': db = 'calibration_instruments'
	else: db = None

	files = __getStateFilenames( ext)
	if files:
		fileSelection = [['Choose file to load',None]]
		for i,k in enumerate( files):
			fileSelection.append( k)
		fileName = screen.menuSelection( fileSelection)
		if fileName == 'q': return
		fn( fileName ,db)
	else:
		screen.show( 'No files found.' ,prompt=True)


def resetDB():
	if screen.confirm( 'WARNING: All test run data will be lost. Proceed?'):
		__defaultDlg( dbConn.pgLoad ,'pce_db_seed.pgd')


def __loadState( fileName ,db=None):
	__defaultDlg( dbConn.pgLoad ,mos.stateDIR + '/' + fileName ,db)
	return 'quit menu'



def __fileNameExists( fileName):
	files = __getStateFilenames()
	if files:
		for f in files:
			if f == fileName:
				return True
	return False

def __defaultDlg( fn ,arg ,db=None):
	screen.show( '''
--------------------------------------------------------------------------------
The procedure may take anywhere from 10 seconds to 10 minutes, depending on the size of the files.\n
A few ERROR messages may appear. This is normal operation.
If multiple ERROR messages appear, please ensure the database
is not being accessed and run the procedure again.''')
	fn( arg ,db)
	screen.show( '\n\nOperation complete. Thank you for your patience.' ,prompt=True)

def __getStateFilenames( ext='.pgd'):
	d = mos.getDirContents( ext)
	if len(d) < 1:
		return False
	return d
