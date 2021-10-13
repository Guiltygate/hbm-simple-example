'''ui'''



import mos
from misc import convert, strs

def clear( num=0):
	mos.clear()
	for i in 0,num:
		print('')

def promptUser():
	get( '\n--- Press ENTER to continue ---')

def get( msg='Enter: ' ,dataType=str ,limit=30 ,format='.*' ,redraw=None ,keyword=False):
	exceededLimit = False

	global input
	try: input = raw_input
	except NameError: pass

	while True:
		resp = input( msg)
		if keyword and resp == 'done': return resp

		resp = convert( resp ,dataType)

		if isinstance( resp ,str):
			resp = strs( format ,resp)
			exceededLimit = (len(resp) > limit)
		elif isinstance( resp ,int):
			exceededLimit = (resp > limit)

		if resp == None or exceededLimit:
			if redraw:
				show( redraw ,True)
				print( '--INVALID ENTRY--')
			else:
				print( 'Invalid entry. Please try again.')
		else:
			return resp

def show( value ,clr=False ,keys=None ,prompt=False):
	if clr: clear()

	if isinstance( value ,dict):
		print( listDisplay( value ,keys))
	elif isinstance( value ,menu):
		value.show()
	else:
		print( value)
	if prompt: promptUser()


def confirm( msg):
	msg = msg + ' (y/n): '
	return get( msg ,bool)

def menuSelection( seed):
	m = menu( seed)
	return m.makeSelection()

def listDisplay( t ,keys):
	pString = ''
	if keys:
		for i in t:
			if i == 0:
				pString = pString + t[i] + "\n------------------------------"
			else:
				pString = pString + '\n' + str(i) + ') '
				for key in keys:
					s = t[i][key]
					pString = pString + s + tabFormat( s)
	else:
		for k in t:
			pString = pString + '\n' + k + ':' + tabFormat( k) + t[k]
	return pString


def tabFormat( str):
	l = len(str)
	if l>20: return '\t'
	elif l>15: return '\t\t'
	elif l>5: return '\t\t\t'
	else: return '\t\t\t\t'


class menu:
	core = None
	title = ''
	returnValue = None

	def __init__( self ,seed):
		self.core = {}
		for i,v in enumerate( seed):
			if i == 0:
				self.title = v[0] + "\n------------------------------"
				self.returnValue = v[1]
			else:
				self.core[i] = {}
				if isinstance( v ,list):
					self.core[i]['text'] = v[0]
					self.core[i]['value'] = v[1]
				else:
					self.core[i]['text'] = v
					self.core[i]['value'] = v
		fi = len( self.core)+1
		if self.returnValue != 'NoQuit':
			self.core[ fi] = {}
			self.core[ fi]['text'] = 'Quit'
			self.core[ fi]['value'] = 'q'


	def liveData( self):
		return isinstance( self.returnValue ,list)

	def show( self):
		pString = '\n\n\n' + self.title
		for i in self.core:
			pString = pString + "\n" + str(i) + ') ' + self.core[i]['text']
			if self.liveData() and i != len(self.core):
				pString = pString + tabFormat( self.core[i]['text']) + (self.returnValue[i] or 'None')
		show( pString ,True)


	def makeSelection( self):
		keyword = False
		while True:
			self.show()
			if self.liveData():
				print( '(Enter "done" when finished)')
				keyword = True
			i = get( '\nPlease make a selection: ' ,int ,len(self.core) ,redraw=self ,keyword=keyword)

			if i == 'done' and self.liveData():
				for v in self.returnValue:
					if not v: return 'q'
				return

			r = None
			value = self.core[i]['value']
			if isinstance( value ,list):
				fn = value[0]
				r = fn( value[1])
			elif hasattr( value ,'__call__'):
				r = value()
			else:
				return value #str, boolean, integer.

			if r:
				if self.liveData():
					self.returnValue[i] = r
				else:
					return r