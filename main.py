#!/usr/bin/python
import os, sys, cherrypy, kid, cjson, config, hashlib, pickle

sys.path.append("%s/lib" % os.path.abspath(sys.path[0]))
from tunnelking import *

log = Log(config.logging, "main.py")
log.log(3, "main.py")

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
		lip = cherrypy.request.remote.ip
		
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
		
		returnDict = {}
		returnDict["apps"] = list(results)
		returnDict["getSms"] = self.checkConnection(lip, id)
		print returnDict
		return pickle.dumps(returnDict)
	getuserini.exposed = True

	def checkOTPKey(self, id, key):
		ip = cherrypy.request.remote.ip
		
		try:
			sql = "DELETE FROM `keys` WHERE `expiretime` < NOW()"
			cherrypy.thread_data.db.execSQL(sql)
		except Exception, e:
			return e
		
		try:	
			sql = "SELECT * FROM `keys` WHERE `key` = '%s' AND `expiretime` > NOW() AND lip = '%s' AND userid = %s" % (key, ip, id)
			print sql
			results = cherrypy.thread_data.db.querySQL(sql)
		except Exception, e:
			return "%s" % e
		
		print results
		
		if len(results):
			sql = "UPDATE `keys` SET trusted = 1 WHERE `key` = '%s' AND `expiretime` > NOW() AND lip = '%s' AND userid = %s" % (key, ip, id)
			print sql
			cherrypy.thread_data.db.execSQL(sql)
			
			os.system("/usr/bin/sudo /usr/bin/qip.py delete %s" % ip)
			return pickle.dumps(True)
		else:
			return pickle.dumps(False)
	
	checkOTPKey.exposed = True
	
	def newSms(self, id):
		try:
			ip = cherrypy.request.remote.ip
			key = OtpKey(config, log)
			
			user = User()
			user.load(id)
			
			key.sendKey(user, ip, "0.0.0.0")
			return pickle.dumps(True)
		except:
			return pickle.dumps(False)
	newSms.exposed = True	
	
	def test(self):
		return "%s" % cherrypy.request.remote.ip
	test.exposed = True
	
	def checkConnection(self, lip, id):
		try:
			sql = "SELECT `trusted` FROM `keys` WHERE lip = '%s' AND userid = %s AND `expiretime` > NOW()" % (lip, id)
			result = cherrypy.thread_data.db.querySQL(sql)
		except Exception, e:
			sys.exit(1)
		
		if len(result) != 0:
			if result[0]['trusted'] == 1:
				return False
			else:
				return True
		else:
			return True
	
	
	
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