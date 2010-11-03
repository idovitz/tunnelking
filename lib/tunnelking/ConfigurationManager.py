
import os, sys, cherrypy, cjson, config, time, types
from Configuration import *
from User import *
from UserManager import *
from DBmysql import *
from copy import copy

class ConfigurationManager:
	def __init__(self):
		self.configurationNames = None
		
	def newConfiguration(self, formdata):
		cherrypy.response.headers['Content-Type'] = 'application/json'
		
		formdata = cjson.decode(formdata)
		print formdata
		
		error = ""
		
		if self.configurations.has_key(formdata["configname"]) == False:
			if formdata["port"] != "":
				if self.checkFreePorts(formdata["protocol"], formdata["port"]):
					formdata["manport"] = self.getFreePorts(formdata["configname"])[1]
				else:
					result = False
					error = "port is occupied"
					return cjson.encode({"result": result, "error": error})
			else:
				freeport = self.getFreePorts(formdata["configname"])
				formdata["port"] = freeport[0]
				formdata["manport"] = freeport[1]
			
			newConf = Configuration(0, formdata["configname"], "")
			newConf.new(formdata)
			
			self.configurations[newConf.id] = copy(newConf)
			self.setConfiguration(newConf.id)
			result = True
		else:
			result = False
			error = "name exists"
		
		self.loadConfigurations()
		
		return cjson.encode({"result": result, "error": error})
	newConfiguration.exposed = True
	
	def saveLdap(self, id, ip, dn, sf, bd, bp):
		
		cherrypy.session['currentconf'].saveLdap
		
		return cjson.encode({"result": result, "error": error})
	
	def savePushOptions(self, optionContainer):
		options = cjson.decode(optionContainer)['options']
		
		result = cherrypy.session['currentconf'].savePushOptions(options)
		
		return cjson.encode({"result": result})
	savePushOptions.exposed = True
	
	def loadPushOptions(self):
		result = cherrypy.session['currentconf'].push

		print type(result)
		if type(result) == types.StringType:
			result = ["%s" % result]
		
		print result
		
		return cjson.encode({"result": result})
	loadPushOptions.exposed = True
	
	def setConfiguration(self, confid):
		cherrypy.response.headers['Content-Type'] = 'application/json'
		
		cherrypy.session['confid'] = confid
		cherrypy.session['currentconf'] = self.configurations[confid]
		
		return cjson.encode({"result": True})
	setConfiguration.exposed = True
	
	def delConfiguration(self, confid):
		cherrypy.response.headers['Content-Type'] = 'application/json'
		
		self.configurations[confid].delete()
		time.sleep(1)
		self.loadConfigurations()
		
		cherrypy.session['confid'] = None
		cherrypy.session['currentconf'] = None
		
		return cjson.encode({"result": True})
	delConfiguration.exposed = True
		
	def loadConfigurations(self):
		self.configurations = {}
		self.configurationNames = []
		
		results = cherrypy.thread_data.db.querySQL("SELECT * FROM configurations ORDER BY name")
		
		for res in results:
			strid = str(res["id"])
			self.configurationNames.append({"confid":res["id"], "name":res["name"]})
			self.configurations[strid] = Configuration(res["id"], res["name"], res["dn"])
			self.configurations[strid].load()
			
	def startConfigurations(self):
		if self.configurationNames == None:
			self.loadConfigurations()
		
		for conf in self.configurations:
			self.configurations[conf].start()
	startConfigurations.exposed = True
	
	def getConfigurationNames(self):
		cherrypy.response.headers['Content-Type'] = 'application/json'

		if self.configurationNames == None:
			self.loadConfigurations()
		
		try:
			if cherrypy.session.get('confid', None) == None and len(self.configurationNames) != 0:
				cherrypy.session['confid'] = self.configurationNames[0]["confid"]		
				cherrypy.session['currentconf'] = self.configurations[str(self.configurationNames[0]["confid"])]
			
			return cjson.encode({"result": [self.configurationNames, int(cherrypy.session['confid'])]})
		except Exception, e:
			print "%s: %s" % (type(e), e)
			return cjson.encode({"result": False})
	getConfigurationNames.exposed = True
	
	def getStatus(self):
		cherrypy.response.headers['Content-Type'] = 'application/json'
		
		try:
			result = self.configurations[str(cherrypy.session['confid'])].getStatus()
		except Exception, e:
			result = [False, "%s: %s" % (type(e), e)]
		
		return cjson.encode({"result": result})
	getStatus.exposed = True
	
	def killConnection(self, cid):
		try:
			self.configurations[str(cherrypy.session['confid'])].connectionManager.kill(cid)
			result = True
		except Exception, e:
			result = [False, "%s: %s" % (type(e), e)]
		
		return cjson.encode({"result": result})
	killConnection.exposed = True
	
	def getUserType(self, id=None):
		if id == None:
			result = {"ldap":cherrypy.session['currentconf']["ldap"]}
		else:
			result = {"ldap":cherrypy.session['currentconf']["ldap"], "id":id}
		
		return cjson.encode({"result": result})
	getUserType.exposed = True
	
	def searchLdapUsers(self, str):
		result = cherrypy.session['currentconf'].lh.search(str)
		
		print result
		
		return cjson.encode({"result": result})
	searchLdapUsers.exposed = True
	
	def stoprestart(self, action):
		if action in ["stop", "start", "restart"]:
			result = self.configurations[str(cherrypy.session['confid'])].__getattribute__(action)()
		else:
			result = False
		
		time.sleep(0.5)
		return cjson.encode({"result": result})
	stoprestart.exposed = True
	
	def getFreePorts(self, confname):
		if len(self.configurations) != 0:
			plist = []
			mlist = []
			for k,conf in self.configurations.iteritems():
				if conf.name != confname:
					plist.append(int(conf.options["port"][0]))
					mlist.append(int(conf.options["management"][1]))
			plist.sort()
			mlist.sort()
			plist.reverse()
			mlist.reverse()
		
			return [plist[0]+1, mlist[0]+1]
		else:
			return [1194, 7500, "udp"]

	def testJson(self, obj):
		print obj
	testJson.exposed = True
		
	def checkFreePorts(self, protocol, port):
		pplist = []
		
		for k,conf in self.configurations.iteritems():
			pplist.append({'port':int(conf.options["port"][0]), 'proto':conf.options["proto"][0]})
		
		for i in pplist:
			if {'port':port, 'proto':protocol} == i:
				return false
    
		return True