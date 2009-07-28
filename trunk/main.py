#!/usr/bin/python

import os, sys, cherrypy, kid, cjson, config

sys.path.append("%s/lib" % os.path.abspath(sys.path[0]))
from tunnelking import *

class Root(object):
	def index(self):
		t = kid.Template('kid/index.xml')
		
		return t.serialize(output="html")
	index.exposed = True
	
	def newconf(self):
		t = kid.Template('kid/newconf.xml')
		
		return t.serialize(output="html")
	newconf.exposed = True
	
	def users(self):
		t = kid.Template('kid/users.xml')
		
		return t.serialize(output="html")
	users.exposed = True
	
	def test(self, info=0):
		cherrypy.response.headers['Content-Type'] = 'application/json'
		return cjson.encode({"result":[info,2,8,1212,2323]})
	test.exposed = True

root = Root()
root.cm = ConfigurationManager()
root.um = UserManager()

cherrypy.quickstart(root, config="cherry.conf")