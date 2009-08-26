#!/usr/bin/python
import os, sys, cherrypy, kid, cjson, config, hashlib

sys.path.append("%s/lib" % os.path.abspath(sys.path[0]))
from tunnelking import *

class Root(object):
	def index(self):
		t = kid.Template('kid/index.xml')
		
		return t.serialize(output="html")
	index.exposed = True
	
	def monitor(self):
		t = kid.Template('kid/monitor.xml')
		
		return t.serialize(output="html")
	monitor.exposed = True
	
	def newconf(self):
		t = kid.Template('kid/newconf.xml')
		
		return t.serialize(output="html")
	newconf.exposed = True
	
	def users(self):
		t = kid.Template('kid/users.xml')
		
		return t.serialize(output="html")
	users.exposed = True
	
	def apps(self):
		t = kid.Template('kid/apps.xml')
		
		return t.serialize(output="html")
	apps.exposed = True

def shatoken(token):
	return hashlib.sha1(token).hexdigest()

def connect(thread_index):
	print "make db instance for thread #%s" % thread_index
	cherrypy.thread_data.db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)

cherrypy.engine.subscribe('start_thread', connect)
	
root = Root()
root.cm = ConfigurationManager()
root.um = UserManager()

cherrypy.quickstart(root, config="cherry.conf")