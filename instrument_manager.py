'''
	instrument_manager
'''


import ui as screen
from psql import psqlConn
from copy import deepcopy
from datetime import date, timedelta
import re

dbConn = psqlConn()



instrumentView = "SELECT DISTINCT \
	cc.name\
	,i.key\
	,cc.manuf_sn\
	,pis.pce_key_name\
	,i.manuf_name\
	,i.model_name\
	,i.dscr\
 FROM current_calequip cc\
	LEFT JOIN instruments i ON cc.manuf_sn = i.manuf_sn\
	LEFT JOIN pce_instr_def pid ON i.key = pid.instr_key\
	LEFT JOIN pce_instr_setup pis ON pid.setup_id = pis.setup_id"

instrumentPresets = {
	 "DMM": 			{'print':True 	,'setup_id':8	,'pce_name':'dmm'}
	,"DC Source": 		{'print':True 	,'setup_id':6 	,'pce_name':'dcsource'}
	,"Function Generator": {'print':True ,'setup_id':12 ,'pce_name':'fgen'}
	,"Power supply": 	{'print':False 	,'setup_id':14 	,'pce_name':'powersupply'}
	,"Electronic load": {'print':False 	,'setup_id':10 	,'pce_name':None}
	,"Rubidium Clock": 	{'print':True 	,'setup_id':0 	,'pce_name':None}
	,"Temp/Humidity Sensor": {'print':True ,'setup_id':18 ,'pce_name':'thsensor'}
	,"Switch matrices": {'print':True 	,'setup_id':16 	,'pce_name':'switchmatrix'}
	,"Burster": 		{'print':True 	,'setup_id':21 	,'pce_name':'burster'}}





def instrumentMenu():
	constructor = [
		 ["Instrument Menu" ,None]
		,['Add Instrument' ,addNewInstrument]
		,['Delete Instrument' ,deleteInstrument]
		,["Exchange / Swap CalStand Instruments" ,exchangeInstruments]
		,["Update calibration record for instrument" ,updateInstrument]
		,["Display instruments equipped on CalStand" ,displayCurrentInstruments]
		,['View instrument Calibration log' ,viewInstrumentCalibrationLog]]
	screen.menuSelection( constructor)


def reloadConnConfig():
	dbConn.loadConfig()

def exchangeInstruments():
	newInstrument = __getInstrument( None ,True)
	if not newInstrument:
		return

	instruments = __getCurrentInstruments( 'pce_key_name')

	oldInstrument = instruments.get( newInstrument['pce_key_name'])
	dI = oldInstrument
	if dI:
		print( 'CalStand already has an instrument fulfilling this role: ' +
			dI['manuf_name'] + ' ' + dI['pce_key_name'] + ' ' + dI['manuf_sn'])
		if not screen.confirm( 'Would you like to replace it?'):
			return

	__transfer( newInstrument ,oldInstrument)

	displayCurrentInstruments()
	if not screen.confirm( 'Does this look correct?'):
		exchangeInstruments()


def __transfer( newInstrument ,oldInstrument=None ,destination=None):
	defaultTransfer = {
		'key': None
		,'instr_key': None
		,'from_loc_key': None
		,'to_loc_key': None
		,'cond_key': None
		,'date': None
		,'notes': "''"}

	if isinstance( newInstrument ,dict):
		newInstrument = newInstrument['key']
	if isinstance( oldInstrument ,dict):
		oldInstrument = oldInstrument['key']

	instruments = {
		 'new': newInstrument
		,'old': oldInstrument}

	for k in instruments:
		instrKey = instruments[k]
		if instrKey:
			nit = deepcopy( defaultTransfer)
			nit['key'] = dbConn.getNextKey( 'transfers' ,'cal')
			nit['instr_key'] = instrKey
			nit['cond_key'] = 1
			nit['date'] = "'" + str(date.today()) + "'"
			nit['from_loc_key'] = __getOldLocationKey( instrKey)

			if k == 'old': nit['to_loc_key'] = 24
			else: nit['to_loc_key'] = destination or __getStationKey()

			dbConn.insert( nit ,'transfers' ,'cal')


def __getStationKey():
	name = dbConn.stationName
	cmd = "SELECT key FROM locations WHERE name = '" + name + "'"
	q = {'cmd': cmd
		,'db': 'cal'
		,'type': 'single'}
	return dbConn.query( q)


def __getOldLocationKey( instrumentKey):
	cmd = "SELECT to_loc_key FROM transfers WHERE key = (SELECT MAX(key) FROM transfers WHERE instr_key = " + str(instrumentKey) + ')'
	q = {'cmd': cmd
		,'db': 'cal'
		,'type': 'single'}	

	r = dbConn.query( q)
	if len(r) == 0:
		return 5
	return r



def __getCurrentInstruments( order=False):
	name = dbConn.stationName
	cmd = instrumentView + " WHERE cc.name = '" + name + "'"
	q = {'cmd': cmd
		,'db': 'cal'
		,'type': 'select'
		,'order': order}
	return dbConn.query( q)

def __insertTitle( t ,title):
	temp = deepcopy( t[0])
	t[0] = title
	t[ len(t)] = deepcopy( temp)


def displayCurrentInstruments():
	instruments = __getCurrentInstruments()
	__insertTitle( instruments ,"Currently Equipped Instruments")

	screen.show( instruments ,True ,['manuf_name','pce_key_name','manuf_sn'] ,True)

def viewInstrumentCalibrationLog( sn=None):
	instr = __getInstrument( sn)
	if not instr: return

	cmd = "SELECT * FROM calibrations WHERE instr_key = " + instr['key']
	q = {
		 'cmd': cmd
		,'db': 'cal'
		,'type': 'select'}
	calibrations = dbConn.query( q)

	pString = 'Calibration Log\n------------------------------'
	for i in calibrations:
		v = calibrations[i]
		pString = pString + '\nCalibrated on ' + v['cal_date'] + ', due on ' + v['due_date']

	screen.show( pString ,True ,prompt=True)




def updateInstrument():
	instr = __getInstrument( None ,True)
	if not instr:
		return

	update = {
		 'key': dbConn.getNextKey( 'calibrations' ,'cal')
		,'instr_key': instr['key']
		,'cal_provider_key': 14 #TODO
		,'start_cond_key': 1
		,'end_cond_key': 1
		,'cal_date': None
		,'due_date': None
		,'cert_loc': "'HBMI'"
		,'notes': "''"}
	calDate = screen.get( 'Please enter the calibration date for the instrument (YYYY-MM-DD): ' 
		,str ,10 ,'\d\d\d\d-\d\d-\d\d')
	r = re.search( '(\d\d\d\d)(-\d\d-\d\d)' ,calDate)
	year ,remainder = int(r.group(1)) ,r.group(2)
	dueDate = str(year + 1) + r.group(2)

	update['cal_date'] = "'" + calDate + "'"
	update['due_date'] = "'" + dueDate + "'"

	dbConn.insert( update ,'calibrations' ,'cal')
	viewInstrumentCalibrationLog( instr['manuf_sn'])


def __getInstrument( sn=None ,canCreate=False):
	screen.clear(4)
	if not sn:
		sn = screen.get( 'Please enter instrument #SN (q to quit): ')
		if sn[0] == 'q': return

	q = {'cmd': instrumentView + " WHERE cc.manuf_sn = '" + sn + "'"
		,'db': 'cal'
		,'type':'select'}
	instr = dbConn.query( q)
	if instr: instr = instr[0]

	if not instr:
		screen.show( 'Instrument does not exist.')
		if canCreate:
			if screen.confirm( 'Would you like to create it?'):
				return addNewInstrument( sn)
			else:
				return False
		else:
			screen.promptUser()
			return False
	else:
		return instr


def __getTHMac():
	screen.clear(4)
	return "'" + screen.get( 'Please enter MAC address for TH Sensor (no colons): ' ,str ,12 ,'\w*') + "'"


def addNewInstrument( sn=None):
	dscrs = [["Instrument Types",None],"DMM","DC Source","Function Generator","Power supply",
	"Electronic load","Rubidium Clock","Temp/Humidity Sensor","Switch matrices","Burster"]


	instrConst = [ 'DummyValue' ,None,None,sn,None]
	addNewInstrumentMenu = [
		 ['Instrument Information' ,instrConst]
		,['Manufacturer Name' ,screen.get]
		,['Model Name' ,screen.get]
		,['Manufacturer Serial Number' ,screen.get]
		,['Description' ,[screen.menuSelection ,dscrs]]]

	q = screen.menuSelection( addNewInstrumentMenu)
	if q: return

	preset = instrumentPresets[ instrConst[4]]

	newInstrKey = dbConn.getNextKey( 'instruments' ,'cal')
	newInstr = {
		 'manuf_name': "'" + instrConst[1] + "'"
		,'model_name': "'" + instrConst[2] + "'"
		,'manuf_sn': "'" + instrConst[3] + "'"
		,'print_on_cert': preset['print']
		,'date_created': "'" + str(date.today()) + "'"
		,'dscr': "'" + instrConst[4] + "'"
		,'key': newInstrKey}
	dbConn.insert( newInstr ,'instruments' ,'cal')

	if preset['pce_name']:
		macSN = (preset['pce_name']=='thsensor' and __getTHMac()) or ("'" + instrConst[3] + "'")
		newIdent = {
			 'instr_key': newInstrKey
			,'pce_name': "'" + preset['pce_name'] + "'"
			,'identifier': macSN
			,'key': dbConn.getNextKey( 'instrument_identifier' ,'cal')}
		dbConn.insert( newIdent ,'instrument_identifier' ,'cal')

	if preset['setup_id']:
		newSetup = {
			'def_id': dbConn.getNextKey( 'pce_instr_def' ,'cal' ,'def_id')
			,'instr_key': newInstrKey
			,'setup_id': preset['setup_id']}
		dbConn.insert( newSetup ,'pce_instr_def' ,'cal')

	__transfer( newInstrKey ,None ,24)

	instr = __getInstrument( instrConst[3])
	showInstrument( instr)
	screen.promptUser()

	return instr

def showInstrument( instr):
	instr['location'] = instr['name']
	del instr['name']
	screen.show( instr ,True)

def deleteInstrument( sn=None):
	instr = __getInstrument( sn)

	showInstrument( instr)
	if screen.confirm( 'Do you wish to delete this instrument? Calibration and transfer logs will remain for posterity.'):
		instrKey = instr['key']
		preset = instrumentPresets[ instr['dscr']]
		if preset['setup_id']:
			dbConn.delete( instrKey ,'instr_key' ,'pce_instr_def' ,'cal')
		if preset['pce_name']:
			dbConn.delete( instrKey ,'instr_key' ,'instrument_identifier' ,'cal')
		dbConn.delete( instrKey ,'key' ,'instruments' ,'cal')

		screen.show( 'Instrument has been removed.' ,True ,prompt=True)






