
from distutils.core import setup
import py2exe

setup(
	console=[
		{
			 'script': 'calstand_db_manager.py'
			,'icon_resources': [(1 ,'pceIcon.ico')]
		}
	]
	,data_files=["pce_db_seed.pgd"]
)