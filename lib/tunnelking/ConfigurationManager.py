
import os, sys, cherrypy, cjson, config, time
from Configuration import *
from User import *
from UserManager import *
from DBmysql import *

class ConfigurationManager:
	def __init__(self):
		self.loadConfigurations()
		
	def newConfiguration(self, configname, domain, o, ou, c, st, l, protocol, port):
		cherrypy.response.headers['Content-Type'] = 'application/json'
		
		error = ""
		
		if self.configurations.has_key(configname) == False:
			
			if protocol != "" and port != "":
				if self.checkFreePorts(protocol, port):
					ports = [port, self.getFreePorts(configname)[1], protocol]
				else:
					result = False
					error = "port is occupied"
					return cjson.encode({"result": result, "error": error})
			else:
				ports = self.getFreePorts(configname)
			
			self.configurations[configname] = Configuration(0, configname, "")
			self.configurations[configname].new(domain, o, ou, c, st, l, ports, ldapDict)
			#self.loadConfigurations()
			
			self.setConfiguration(self.configurations[configname].id)
			result = True
		else:
			result = False
			error = "name exists"
					
		return cjson.encode({"result": result, "error": error})
	newConfiguration.exposed = True
	
	def saveLdap(self, id, ip, dn, sf, bd, bp):
		
		cherrypy.session['currentconf'].saveLdap
		
		return cjson.encode({"result": result, "error": error})
		
	def setConfiguration(self, confid):
		cherrypy.response.headers['Content-Type'] = 'application/json'
		
		cherrypy.session['confid'] = confid
		cherrypy.session['currentconf'] = self.configurations[confid]
		
		return cjson.encode({"result": True})
	setConfiguration.exposed = True
	
	def delConfiguration(self, confid):
		cherrypy.response.headers['Content-Type'] = 'application/json'
		
		self.configurations[confid].delete()
		self.loadConfigurations()
		
		cherrypy.session['confid'] = None
		cherrypy.session['currentconf'] = None
		
		return cjson.encode({"result": True})
	delConfiguration.exposed = True
		
	def loadConfigurations(self):
		self.configurations = {}
		self.configurationNames = []
		
		db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
		results = db.querySQL("SELECT * FROM configurations")
		
		for res in results:
			strid = str(res["id"])
			self.configurationNames.append({"confid":res["id"], "name":res["name"]})
			self.configurations[strid] = Configuration(res["id"], res["name"], res["dn"])
			self.configurations[strid].load()
		
	def getConfigurationNames(self):
		cherrypy.response.headers['Content-Type'] = 'application/json'
		
		try:
			if cherrypy.session.get('confid', None) == None and len(self.configurationNames) != 0:
				cherrypy.session['confid'] = self.configurationNames[0]["confid"]		
				cherrypy.session['currentconf'] = self.configurations[str(self.configurationNames[0]["confid"])]
			
			if len(self.configurationNames) == 0:
				self.loadConfigurations()
			
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
	
	def checkFreePorts(self, protocol, port):
		pplist = []
		
		for k,conf in self.configurations.iteritems():
			pplist.append({'port':int(conf.options["port"][0]), 'proto':conf.options["proto"][0]})
		
		for i in pplist:
			if {'port':port, 'proto':protocol} == i:
				return false
		
		return True