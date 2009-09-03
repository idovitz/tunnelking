#!/usr/bin/python
import os, sys, cherrypy, kid, cjson, config, hashlib, pickle

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
	
	def getuserini(self, id):
		sql = "SELECT us.id, app.appname, app.autostart FROM users AS us JOIN apps_users AS app ON app.userid = us.id WHERE us.id = %s" % id
		results = cherrypy.thread_data.db.querySQL(sql)
		
		for app in results:
			f = open("%s/apps/%s/__info__" % (sys.path[0], app["appname"]), "r")
			lines = f.readlines()
			f.close()
			
			params = {}
			for line in lines:
				spline = line.strip().split("=")
				params[spline[0]] = spline[1]
			
			app["currentversion"] = params["VERSION_PRODUCTION"]
		
		return pickle.dumps(list(results))
	getuserini.exposed = True

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