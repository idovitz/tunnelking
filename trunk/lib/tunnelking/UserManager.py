##################################################
# projectname: tunnelking
# Copyright (C) 2009  IJSSELLAND ZIEKENHUIS
##################################################

import cherrypy, cjson, config, operator
from DBmysql import *
from User import *

class UserManager:
	def __init__(self):
		self.users = {}
		self.loadUsers()
		
	def loadUsers(self):
		self.users = {}
		
		# get all users
		db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
		results = db.querySQL("SELECT id, confid FROM users")
		
		# load users in dict
		for res in results:
			if not self.users.has_key(res["confid"]):
				self.users[res["confid"]] = {}
			
			self.users[res["confid"]][res['id']] = User()
			self.users[res["confid"]][res['id']].load(res['id'])
	
	def getUsers(self):
		return self.users
		
	def getUserNames(self):
		cherrypy.response.headers['Content-Type'] = 'application/json'
		
		confid = int(cherrypy.session['confid'])
		
		if self.users.has_key(confid):
			print self.users[confid]
			results = []
			
			users = self.users[confid].values()
			users.sort(key=lambda obj: obj["name"])
			
			for user in users:
				print user
				results.append({'id':user["id"], 'name':user["name"]})
		else:
			results = False
			
		return cjson.encode({'result':results})
	getUserNames.exposed = True
	
	def addUser(self, name, password):
		confid = int(cherrypy.session['confid'])
		
		newuser = User()
		results = newuser.new(name, password, confid)
		
		if results:
			if self.users.has_key(confid) == False:
				self.users[confid] = {}
			
			self.users[confid][newuser['id']] = newuser
		
		return cjson.encode({'result':results})
	addUser.exposed = True
	
	def delUser(self, id):
		confid = int(cherrypy.session['confid'])
		
		results = self.users[confid][int(id)].delete()
		
		self.loadUsers();
		
		return cjson.encode({'result':results})
	delUser.exposed = True
	
	def getUserPackage(self, id):
		confid = int(cherrypy.session['confid'])
		
		results = self.users[confid][int(id)].getPackage()
		
		return cjson.encode({'result':results})
	getUserPackage.exposed = True
	
	def delUsers(self, confid):
		self.users[confid] = None