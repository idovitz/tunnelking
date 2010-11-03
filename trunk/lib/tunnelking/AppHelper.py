'''
Created on 3 nov. 2010

@author: ido
'''
import os
import sys
import config

class AppHelper:
	@staticmethod
	def getCurrentVersion(appname, testdriver):
		params = AppHelper.getParams(appname)
		
		if os.path.exists("%s/apps/%s/%s.tar.bz2" % (sys.path[0], appname, params["VERSION_TEST"])) and testdriver == 1:
			return params["VERSION_TEST"]
		else:
			return params["VERSION_PRODUCTION"]
	
	@staticmethod
	def getAllAppNames():
		for root, dirs, files in os.walk("%s/apps" % config.basemap): #@UnusedVariable
			appnames = dirs
			break
		
		for appname in appnames:
			if appname.find("__") != -1 or appname.find(".") != -1:
				appnames.remove(appname)
				
		return appnames
	
	@staticmethod
	def getDependencies():
		depends = {}
		
		for appname in AppHelper.getAllAppNames():
			params = AppHelper.getParams(appname)
			
			if "DEPEND" in params.keys():
				depends[appname] = params["DEPEND"]
		
		return depends
		
	@staticmethod	
	def getParams(appname):
		f = open("%s/apps/%s/__info__" % (sys.path[0], appname), "r")
		lines = f.readlines()
		f.close()
		
		params = {}
		for line in lines:
			spline = line.strip().split("=")
			params[spline[0]] = spline[1]
		
		return params
		