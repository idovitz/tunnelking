#!/usr/bin/python
import os, sys, cherrypy, kid, cjson, config, hashlib, pickle

sys.path.append("%s/lib" % os.path.abspath(sys.path[0]))
from tunnelking import *
from urllib import quote, unquote

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
	
	def key(self, userid):
		t = kid.Template('kid/key.xml')
		t.userid = userid
		return t.serialize(output="html")
	key.exposed = True
	
	def getuserini(self, id):
		lip = cherrypy.request.remote.ip
		
		sql = "SELECT us.testdriver FROM users AS us WHERE us.id = %s" % id
		results = cherrypy.thread_data.db.querySQL(sql)
		testdriver = list(results)[0]["testdriver"]
		
		sql = "SELECT us.id, us.testdriver, app.appname, app.autostart FROM users AS us JOIN apps_users AS app ON app.userid = us.id WHERE us.id = %s" % id
		results = cherrypy.thread_data.db.querySQL(sql)
		results = list(results)
		
		results.append({"appname":"__base__", "autostart":0})
		
		for app in results:
			app["currentversion"] = AppHelper.getCurrentVersion(app["appname"], testdriver)
		
		returnDict = {}
		returnDict["apps"] = list(results)
		if self.checkOTP(id):
			returnDict["getSms"] = self.checkConnection(lip, id)
		else:
			returnDict["getSms"] = False
		print returnDict
		return pickle.dumps(returnDict)
	getuserini.exposed = True
	
	def putversions(self, id, versions):
		versions = pickle.loads(unquote(versions))
		
		print "%s: %s" % (id, versions)
		
		for app in versions:
			try:
				sql = "INSERT INTO userversions  (userid, appname, version) VALUES(%s, '%s', %s) ON DUPLICATE KEY UPDATE version = %s" % (id, app, versions[app], versions[app])
				print sql
				cherrypy.thread_data.db.execSQL(sql)
			except Exception, e:
				print e
				return e
		
	putversions.exposed = True

	def checkOTPKey(self, id, key):
		ip = cherrypy.request.remote.ip
		rip = self.getRemoteAddr(ip)
		
		try:
			sql = "DELETE FROM `keys` WHERE `expiretime` < NOW()"
			cherrypy.thread_data.db.execSQL(sql)
		except Exception, e:
			return e
		
		try:	
			sql = "SELECT * FROM `keys` WHERE `key` = '%s' AND `expiretime` > NOW() AND rip = '%s' AND userid = %s" % (key, rip, id)
			print sql
			results = cherrypy.thread_data.db.querySQL(sql)
		except Exception, e:
			return "%s" % e
		
		print results
		
		if len(results):
			sql = "UPDATE `keys` SET trusted = 1 WHERE `key` = '%s' AND `expiretime` > NOW() AND rip = '%s' AND userid = %s" % (key, rip, id)
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
			
			key.sendKey(user, ip, self.getRemoteAddr(ip))
			return pickle.dumps(True)
		except:
			return pickle.dumps(False)
	newSms.exposed = True
	
	def getRemoteAddr(self, ip):
		sql = "SELECT userid, rip FROM `connections` WHERE lip = '%s'" % ip
		result = cherrypy.thread_data.db.querySQL(sql)
		if len(result) != 0:
			return result[0]["rip"]
		else:
			return False

	def test(self):
		return "%s" % cherrypy.request.remote.ip
	test.exposed = True
	
	def checkConnection(self, lip, id):
		rip = self.getRemoteAddr(lip)
		
		try:
			sql = "SELECT `trusted` FROM `keys` WHERE rip = '%s' AND userid = %s AND `expiretime` > NOW() ORDER BY expiretime DESC LIMIT 1" % (rip, id)
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
	
	def checkOTP(self, id):
		try:
			sql = "SELECT id, otpRecipient FROM users WHERE id = %s" % (id)
			result = cherrypy.thread_data.db.querySQL(sql)
		except Exception, e:
			sys.exit(1)
		
		if result[0]["otpRecipient"] != "":
			return True
		else:
			return False
	
	
	
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