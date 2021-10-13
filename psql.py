'''
	Author: Eric Ames
	Date: 2015-12
	Rev: 2016-03
	Attempt at generic PSQL python in-between.
	Requires PostgreSQL at 8.1 or newer be installed
		(configured only for 8.3/8.4/9.3)
	Tested for Ubuntu-like distros and Windows XP/7
'''
import re
import mos
from sys import platform as OS
import ui as screen
import pickle
from copy import deepcopy

class psqlConn:
	delimiter = '|'
	pathBuilding = {
		'elements': [ 'C:' ,'','PostgreSQL' ,'' ,'bin']
		,'psqlVersions': [ '8.3' ,'8.4' ,'9.3']
		,'programFolders': [ 'Progra~1' ,'Progra~2']
	}	
	path = ""
	exe = ""
	dbs = { 'cal':"calibration_instruments" ,'hbm':'hbmsomat'}
	args = { 
		 'host': 'localhost' 
		,'db': 'hbm'
		,'User': 'postgres'
		,'cmd': ''}
	sampleQuery = {'cmd':"SELECT * FROM uut_result WHERE run_id = '00000000-0000-0000-0000-000000000000'",'db':'hbm','type':'select'}
	stationName = ''
	initialSetup = True
	#---------------------------------------------------

	def __init__( self):
		self.loadConfig()
		self.checkPGPass()
		self.OS = OS
		if self.OS == 'win32':
			self._windowsSetup()
		else:
			self._linuxSetup()

	def _windowsSetup( self):
		for pf in self.pathBuilding['programFolders']:
			self.pathBuilding['elements'][1] = pf				
			for version in self.pathBuilding['psqlVersions']:
				self.pathBuilding['elements'][3] = version

				self.__buildPath()
				if self.query( deepcopy(self.sampleQuery)):
					print( 'Found psql install.')
					initialSetup = False
					return
		raise Exception("Couldn't find psql path.")		

	def __buildPath( self):
		s = ""
		for string in self.pathBuilding['elements']:
			s = s + string + '\\'
		self.path = s

	def _linuxSetup( self):
			self.path = ''
			initialSetup = False
			self.query( deepcopy(self.sampleQuery))
			return

	def __buildQueryCmd( self):
		args = ''
		for key in self.args:
			char = key[0]
			args = args + '-' + char + ' ' + self.args[ key] + ' '
		if self.OS == 'win32':
			r = self.path + self.exe + '.exe ' + args
		else:
			r = self.path + self.exe + ' ' + args
		return r


	def __checkQueryResponse( self ,resp):
		if isinstance( resp ,str) and re.search( self.delimiter ,resp):
			return True
		return False

	def __updateQueryArgs( self ,t):
		for k in t:
			if k == 'db':
				self.args.pop( k ,None) #For psql statements that don't accept db args
				if t[k] != None:
					self.args[k] = self.dbs[ t[k]]
			else:
				self.args[ k] = t[ k]

	def __parse( self ,blob):
		if re.search( '\(0 rows\)' ,blob):
			return []

		result = []
		lineList = re.split( "\n" ,blob)
		lineList.pop(1) #shed empty line between schema and values
		for line in lineList:
			line = self.delimiter + ' ' + line + ' ' + self.delimiter
			valueList = re.split( '\s*\|\s*' ,line)
			valueList.pop(); valueList.pop(0) #-- shed splitting errors
			result.append( valueList)
		result.pop();result.pop();result.pop();
		return result

	def __schemaParse( self ,t ,order=None):
		schema = t.pop(0)
		newT = {}
		for i,row in enumerate(t):
			newT[i] = {}
			for j,name in enumerate(schema):
				newT[i][name] = row[j]
		if order:
			orderedT = {}
			for key in newT:
				orderValue = newT[ key][ order]
				orderedT[ orderValue] = newT[ key]
			return orderedT
		else:
			return newT


	def __formatListToStatement( self ,t ,tableName):
		c = "INSERT INTO " + tableName + " ("
		for key in t:
			c = c + key + ','
		c = c[:-1] + ') VALUES ('
		for key in t:
			c = c + str(t[key]) + ','
		c = c[:-1] + ')'
		return c

	def __runQuery( self ,q ,getResponse=False):
		self.__updateQueryArgs( q)

		queryCmd = self.__buildQueryCmd()

		resp = mos.cmd( queryCmd)
		if not getResponse:
			return
		elif self.__checkQueryResponse( resp):
			return self.__parse( resp)
		elif not self.initialSetup:
			raise Exception('No response from server.')
			

	#returns every (successful) query as a list of lists.
	# first hierarchy is by rows (newlines), second is by columns (delimiters)
	def query( self ,q):

		if not q.get('type'):
			return self.__runQuery( q ,True)
		else:
			getResponse = False
			qType = q.pop('type')

			if qType == 'insert':
				q['cmd'] = self.__formatListToStatement( q['cmd'] ,q.pop('table'))
				getResponse = False
			elif qType == 'single':
				getResponse = True
			elif qType == 'select':
				getResponse = True
				if q.get('order') or q.get('order') == False:
					order = q.pop('order')
				else:
					order = None

			self.exe = 'psql'
			q['cmd'] = '"' + q['cmd'] + ';"'			
			resp = self.__runQuery( q ,getResponse)

			if (isinstance( resp ,dict) or isinstance( resp ,list))\
			and	len(resp) > 0:
				if qType == 'single':
					return resp[1][0]
				elif qType == 'select':
					resp = self.__schemaParse( resp ,order)

			if resp == False:
				Exception( 'Query failed.')

			return resp


	def insert( self ,t ,table ,db):
		q = {
			 'table':table
			,'cmd':t
			,'type':'insert'
			,'db': db}
		return self.query( q)

	def delete( self ,v ,key ,table ,db):
		cmd = "DELETE FROM " + table + " WHERE " + key + " = '" + v + "'"
		q = {
			 'cmd': cmd
			,'type': 'delete'
			,'db': db
		}
		return self.query( q)

	def getNextKey( self ,table ,db ,name='key'):
		cmd = 'SELECT MAX(' + name + ') from ' + table
		q = {
			'cmd': cmd
			,'db': db
			,'type': 'single'
		}
		instrKey = self.query( q)
		return int(instrKey) + 1


	def pgDump( self ,fileName ,db=None):
		self.exe = 'pg_dumpall'
		q = {
			'cmd': ' > ' + fileName
			,'db': None}
		self.query( q)


	def pgLoad( self ,fileName ,db=None):
		self.exe = 'psql'
		cmd = self.path + self.exe + \
			" -U postgres -h " + self.args['host']
		if db:
			cmd = cmd + ' -d ' + db
		cmd = cmd + " < " + fileName
		mos.cmd( cmd)
		print( cmd)


	def loadConfig( self):
		try:
			fh = open( '.config' ,'rb')
			G = pickle.load( fh)
			self.args['host'] = G['host']
			self.stationName = G['station']

		except Exception:
			self.configSetup()


	def configSetup( self):
		G = {}
		hostSelection = [
			 ["Host Selection" ,'NoQuit']
			,['Localhost (Your PC)' ,'localhost']
			,['Iris (US, Champaign)' ,'iris.somat.com']
			,['Aello (US, Marlborough)' ,'aello.hbm.com']
			,['Ocypete (UK, London)' ,'ocypete.hbm.com']]
		stationSelection = [
			 ['Station Selection' ,'NoQuit']
			,['CAT China' ,'cs08']
			,['CAT PPG' ,'cs03']
			,['CS01' ,'cs01']
			,['CS02' ,'cs02']
			,['CS04' ,'cs04']
			,['CS05' ,'cs05']
			,['CS06' ,'cs06']
			,['CS07' ,'cs07']]

		G['station'] = screen.menuSelection( stationSelection) + '-teststand'
		if G['station'] == 'cs08-teststand' or G['station'] == 'cs03-teststand':
			G['host'] = 'localhost'
		else:
			G['host'] = screen.menuSelection( hostSelection)
		self.saveConfig( G)
		self.loadConfig()


	#Used to save default settings for hostname and stationname
	def saveConfig( self ,obj):
		mos.cmd( 'rm .config')
		fh = open( '.config' ,'wb')
		pickle.dump(obj ,fh)
		fh.close()

	def isTriptych(self):
		if self.args['host'] == 'iris.somat.com' or\
			self.args['host'] == 'ocypete.hbm.com' or\
			self.args['host'] == 'aello.hbm.com':
			return True
		else:
			return False

	def checkPGPass(self):
		line = self.args['host'] + ':5432:*:postgres:wibble\n'
		try:
			fh = open( mos.pgPass ,'r')
			a = fh.read()
			if isinstance( a.index( line) ,int):
				return			
		except Exception:
			pass

		fh = open( mos.pgPass ,'w')
		fh.write( line)
		fh.close()
		mos.setPermission( '0600' ,mos.pgPass)




