from distutils.core import setup
import py2exe
opts = {
	'py2exe': { 
			'includes': "pango,atk,gobject",
	          }
	}
	
setup(name='Free Poker Database', version='0.12', console=[{"script":"fpdb.py"}])

