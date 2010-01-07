##################################################
# projectname: tunnelking
# Copyright (C) 2009  IJSSELLAND ZIEKENHUIS
##################################################

import cherrypy, cjson, config, operator, os
from DBmysql import *
from User import *
from copy import copy
from types import NoneType

class UserManager:
	def __init__(self):
		self.users = {}
		self.loaded = 0
		
	def loadUsers(self):
		self.users = {}
		
		# get all users
		results = cherrypy.thread_data.db.querySQL("SELECT id, confid FROM users")
		
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
		
		#if not self.loaded:
		self.loadUsers()
		self.loaded = 1
		
		confid = int(cherrypy.session['confid'])
		
		if self.users.has_key(confid):
			results = []
			
			users = self.users[confid].values()
			users.sort(key=lambda obj: obj["name"])
			
			for user in users:
				print type(user["lastlogin"])
				
				if type(user["lastlogin"]) != NoneType:
					lastlogin = user["lastlogin"].strftime("%d-%m-%Y %H:%M")
				else:
					lastlogin = ""
				
				results.append({'id':user["id"], 'name':user["name"], "lastlogin":lastlogin})
		else:
			results = False
			
		return cjson.encode({'result':results})
	getUserNames.exposed = True
	
	def addUser(self, formdata):
		confid = int(cherrypy.session['confid'])
		formdata = cjson.decode(formdata)
		
		newuser = User()
		results = newuser.new(formdata, confid)
		
		if results:
			if self.users.has_key(confid) == False:
				self.users[confid] = {}
			
			self.users[confid][newuser['id']] = newuser
		
		return cjson.encode({'result':results})
	addUser.exposed = True
	
	def saveUser(self, id, formdata):
		confid = int(cherrypy.session['confid'])
		formdata = cjson.decode(formdata)
		user = self.users[confid][int(id)]
		
		result = user.save(formdata)
		
		return cjson.encode({'result':result})
	saveUser.exposed = True	
		
	
	def getUserInfo(self, id):
		confid = int(cherrypy.session['confid'])
		user = self.users[confid][int(id)]
		results = {'id':user["id"], 'name':user["name"], 'otpRecipient':user["otpRecipient"], 'keypin':(user["keypin"] != "")}
		
		return cjson.encode({'result':results})
	getUserInfo.exposed = True
	
	def getUserAppInfo(self, id):
		confid = int(cherrypy.session['confid'])
		user = self.users[confid][int(id)]
		results = {'appversions':user.getAppVersions()}
		
		return cjson.encode({'result':results})
	getUserAppInfo.exposed = True
	
	def getUserApps(self, id):
		result = {}
		
		# get user apps
		confid = int(cherrypy.session['confid'])
		user = self.users[confid][int(id)]
		result['userapps'] = user.apps
		
		# get all apps
		for root, dirs, files in os.walk("%s/apps" % config.basemap):
			result['availapps'] = dirs
			break
		
		availapps = copy(result['availapps'])
		for app in availapps:
			if app in result['userapps'] or app.find("__") != -1 or app.find(".") != -1:
				result['availapps'].remove(app)
				
		result["autostart"] = user.autostart
		
		return cjson.encode({'result':result})
	getUserApps.exposed = True
	
	def saveUserApps(self, id, apps, autostart):
		confid = int(cherrypy.session['confid'])
		user = self.users[confid][int(id)]
		result = user.saveApps(cjson.decode(apps)["names"], autostart)
		
		return cjson.encode({'result':result})
	saveUserApps.exposed = True
	
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