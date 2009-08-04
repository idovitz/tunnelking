##################################################
# projectname: tunnelking
# Copyright (C) 2009  IJSSELLAND ZIEKENHUIS
##################################################

import config, cherrypy, zipfile, time
from DBmysql import *

class User(object):
	def __init__(self):
		self.data = {}
			
	def __setitem__(self, key, item):
		self.data[key] = item
		
	def __getitem__(self, key):
		return self.data[key]
	
	def new(self, name, password, confid):
		try:
			db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
			db.execSQL("INSERT INTO users (confid, name, password) VALUES(%s, '%s', '%s')" % (confid, name, password))
			self.data['id'] = db.cursor.lastrowid
			self.load(self.data['id'])
			
			cherrypy.session['currentconf'].ch.createUserKey("%s.users.%s" % (name, cherrypy.session['currentconf'].dn))
			return True
		except Exception, e:
			print type(e), e
			return False
	
	def delete(self):
		try:
			db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
			db.execSQL("DELETE FROM users WHERE id = %s" % self.data['id'])
			cherrypy.session['currentconf'].ch.delUserKey("%s.users.%s" % (self.data['name'], cherrypy.session['currentconf'].dn))
			return True
		except Exception, e:
			print e
			return False
		
	
	def load(self, userid):
		db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
		results = db.querySQL("SELECT * FROM users WHERE id = %s" % userid)
		
		for key, item in results[0].iteritems():
			self[key] = item
			
	def getKeyCert(self):
		return cherrypy.session['currentconf'].ch.getUserKey("%s.users.%s" % (self.data['name'], cherrypy.session['currentconf'].dn), self.data['password'])
	
	def getPackage(self):
		kc = self.getKeyCert()
		
		# open zip
		zf = zipfile.ZipFile("tmp/%s.%s.zip" % (self.data["name"], cherrypy.session['currentconf'].dn), "w")
		
		# write cert/key to zip
		now = time.localtime(time.time())[:6]
		for k, v in kc.iteritems():
			zfk = zipfile.ZipInfo("openvpn/config/%s" % k)
			zfk.date_time = now
			zfk.compress_type = zipfile.ZIP_DEFLATED
			zf.writestr(zfk, v)
		
		zf.close()
		
		return True
	
	def __str__(self):
		str = "{"
		co = ""
		for key, data in self.data.iteritems():
			str = str+"%s'%s':%s" % (co, key, data)
			co = ", "
		
		str = str+"}"
		return str