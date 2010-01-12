##################################################
# projectname: tunnelking
# Copyright (C) 2009  IJSSELLAND ZIEKENHUIS
##################################################

import cherrypy
from DBmysql import *
from UserPackage import UserPackage

class User(object):
	def __init__(self):
		self.data = {}
		self.autostart = ""
			
	def __setitem__(self, key, item):
		self.data[key] = item
		
	def __getitem__(self, key):
		return self.data[key]
	
	def new(self, formdata, confid):
		if not formdata.has_key("password"):	
			formdata["password"] = "niks"
			
		try:
			cherrypy.thread_data.db.execSQL("INSERT INTO users (confid, name, keypin, password, otpRecipient) VALUES(%s, '%s', '%s', SHA1('%s'), '%s')" % (confid, formdata['name'], formdata['keypin'], formdata["password"], formdata["otpRecipient"]))
			self.data['id'] = cherrypy.thread_data.db.cursor.lastrowid
			self.load(self.data['id'])
			
			cherrypy.session['currentconf'].ch.createUserKey("%s.users.%s" % (formdata['name'], cherrypy.session['currentconf'].dn))
			return True
		except Exception, e:
			print type(e), e
			return False
	
	def save(self, formdata):
		try:
			if formdata.has_key("keypin"):
				if formdata["keypin"] != "":
					keyPinSql = "keypin = '%s'," % formdata["keypin"]
				else:
					keyPinSql = ""
			else:
				keyPinSql = "keypin = '',"
			
			if formdata["password"] == "":
				passSql = ""
			else:
				passSql = "password = SHA1('%s')," % formdata['password']
			
			if formdata.has_key("otpRecipient"):
				if formdata["otpRecipient"] != "":
					otpSql = "otpRecipient = '%s'" % formdata["otpRecipient"]
				else:
					otpSql = ""
			else:
				otpSql = "otpRecipient = ''"
				
			
			sql = "UPDATE users SET %s %s %s WHERE id = %s" % (keyPinSql, passSql, otpSql, self.data['id'])
			cherrypy.thread_data.db.execSQL(sql)
			self.load(self.data['id'])
			return True
		except Exception, e:
			print type(e), e
			return False
		
	
	def delete(self):
		try:
			cherrypy.thread_data.db.execSQL("DELETE FROM users WHERE id = %s" % self.data['id'])
			cherrypy.thread_data.db.execSQL("DELETE FROM apps_users WHERE userid = %s" % self.data['id'])
			cherrypy.thread_data.db.execSQL("DELETE FROM userversions WHERE userid = %s" % self.data['id'])
			cherrypy.session['currentconf'].ch.delUserKey("%s.users.%s" % (self.data['name'], cherrypy.session['currentconf'].dn))
			return True
		except Exception, e:
			print e
			return False
		
	
	def load(self, userid):
		try:
			results = cherrypy.thread_data.db.querySQL("SELECT * FROM users WHERE id = %s" % userid)
		except:
			results = {}
		
		for key, item in results[0].iteritems():
			self[key] = item
		
		self.loadApps()
	
	def loadApps(self):
		results = []
		
		try:
			result = cherrypy.thread_data.db.querySQL("SELECT appname, autostart FROM apps_users WHERE userid = %s" % self.data['id'])
		except:
			result = {}
			
		for item in result:
			results.append(item["appname"])
			if item["autostart"] == 1:
				self.autostart = item["appname"]
			
		self.apps = results
		
	def saveApps(self, apps, autostart):
		try:
			cherrypy.thread_data.db.execSQL("DELETE FROM apps_users WHERE userid = %s" % self.data['id'])
			
			
			for app in apps:
				if autostart == app:
					auto = 1
				else:
					auto = 0
				 
				cherrypy.thread_data.db.execSQL("INSERT INTO apps_users (appname, userid, autostart) VALUES('%s', %s, %s)" % (app, self.data['id'], auto))
				
			self.loadApps()
			return True
		except:
			return False
	
	def getAppVersions(self):
		results = {}
		
		try:
			result = cherrypy.thread_data.db.querySQL("SELECT appname, version FROM userversions WHERE userid = %s" % self.data['id'])
		except:
			result = {}
			
		for item in result:
			results[item["appname"]] = item["version"]
			
		return results
			
	def getKeyCert(self):
		return cherrypy.session['currentconf'].ch.getUserKey(self.data['name'], cherrypy.session['currentconf'].dn, self.data['keypin'])
	
	def getExpireDate(self):
		return cherrypy.session['currentconf'].ch.getExpireDate(self.data['name'], cherrypy.session['currentconf'].dn, self.data['keypin'])
	
	def getPackage(self):
		package = UserPackage(self.data["id"], self.data["name"], cherrypy.session['currentconf'].dn, self.getKeyCert(), self.apps)
		
		return package.filename
	
	
	
	def __str__(self):
		str = "{"
		co = ""
		for key, data in self.data.iteritems():
			str = str+"%s'%s':%s" % (co, key, data)
			co = ", "
		
		str = str+"}"
		return str