
import zipfile, time, cherrypy, config, os #@UnresolvedImport

class UserPackage:
	def __init__(self, userid, username, dn, keycert, apps, testdriver):
		self.filename = "tmp/%s.%s.zip" % (username, dn)
		self.username = username
		self.dn = dn
		self.userid = userid
		self.testdriver = testdriver
		
		# open zip
		self.zipFile = zipfile.ZipFile(self.filename, "w")
		
		# apps
		self.appDirs(apps)
		
		# write cert/key to zip
		for k, v in keycert.iteritems():
			self.writeString("PortableApps/OpenVPNPortable/data/config/%s" % k, v)
			
		self.userConfigFile()
			
	def writeString(self, name, str):
		now = time.localtime(time.time())[:6]
		
		zfk = zipfile.ZipInfo(name)
		zfk.date_time = now
		zfk.compress_type = zipfile.ZIP_DEFLATED
		self.zipFile.writestr(zfk, str)
		
	def writeFile(self, path, name):		
		self.zipFile.write(path, name, zipfile.ZIP_DEFLATED)
	
	def userConfigFile(self):
		tlsremote = "\"/CN=server.%s/O=%s/OU=%s/C=%s/ST=%s/L=%s\"" % (
																		cherrypy.session['currentconf']["domain"], #@UndefinedVariable
																		cherrypy.session['currentconf']["o"], #@UndefinedVariable
																		cherrypy.session['currentconf']["ou"], #@UndefinedVariable
																		cherrypy.session['currentconf']["c"], #@UndefinedVariable
																		cherrypy.session['currentconf']["st"], #@UndefinedVariable
																		cherrypy.session['currentconf']["l"] #@UndefinedVariable
																		)
		
		server = cherrypy.session['currentconf'].options["server"][0]
		ss = server.split(".")
		server = ""
		dot = ""
		for s in ss:
			if ss.index(s) == 3:
				s = "1"
			server += "%s%s" % (dot, s)
			dot = "."
		
		options = {
				   "client":[],
				   "dev":["tun"],
				   "port":cherrypy.session['currentconf'].options["port"],
				   "proto":cherrypy.session['currentconf'].options["proto"],
				   "tls-client": [],
				   "ca": ["ca.%s.cert" % cherrypy.session['currentconf'].dn],
				   "cert": ["%s.users.%s.cert" % (self.username, cherrypy.session['currentconf'].dn)],
				   "key": ["%s.users.%s.key" % (self.username, cherrypy.session['currentconf'].dn)],
				   "tls-auth": ["ta.%s.key" % cherrypy.session['currentconf'].dn, "1"],
				   "remote": [cherrypy.session['currentconf']["remoteip"]], #@UndefinedVariable
				   "tls-remote": [tlsremote.replace(" ", "_")],
				   "pull": [],
				   "auth-user-pass": [],
				   "reneg-sec": ["0"],
				   "comp-lzo": [""],
				   "up": ["\"start /B ..\\\start\\\start.exe --ip %s --id %s --mo updater\"" % (server, self.userid)],
				   "script-security": ["3", "system"]
		}
		
		str = "# automagicaly generated by the king of tunnels\n"
		
		for k, v in options.iteritems():
			line = "%s" % k
			for o in v:
				line = "%s %s" % (line, o)
			
			line = line+"\n"
			str = str+line
		
#		self.writeString("/data/config/%s.users.%s.ovpn" % (self.username, self.dn), str)
		self.writeString("PortableApps/OpenVPNPortable/data/config/client.ovpn", str)
	
	def getAppInfo(self, app):
		infofile = open("%s/apps/%s/__info__" % (config.basemap, app), "r")
		lines = infofile.readlines()
		
		info = {}
		for infoLine in lines:
			spline = infoLine.strip().split("=")
			info[spline[0]] = spline[1]
		
		return info
		
	def appDirs(self, apps):
		# Selected apps
		for app in apps:
			appinfo = self.getAppInfo(app)
			if self.testdriver == 1 and os.path.exists("%sapps/%s/%s/" % (config.basemap, app, appinfo["VERSION_TEST"])):
				version = appinfo["VERSION_TEST"]
			else:
				version = appinfo["VERSION_PRODUCTION"]
			
			for r, d, f in os.walk("%sapps/%s/%s" % (config.basemap, app, version)):
				for file in f:
					if file.find("__") != -1 or file[0] != ".":
						filepath = "%s/%s" % (r,file)
						name = "PortableApps/%s/%s" % (app, filepath.replace("%sapps/%s/%s/" % (config.basemap, app, version), ""))
						self.writeFile(filepath, name)
		
		# base files
		appinfo = self.getAppInfo("__base__")
		if self.testdriver == 1 and os.path.exists("%sapps/__base__/%s/" % (config.basemap, appinfo["VERSION_TEST"])):
			version = appinfo["VERSION_TEST"]
		else:
			version = appinfo["VERSION_PRODUCTION"]
			
					
		for r, d, f in os.walk("%sapps/__base__/%s" % (config.basemap, version)):
			app = "__base__"
			for file in f:
				if file.find("__") != -1 or file[0] != ".":
					filepath = "%s/%s" % (r,file)
					name = "%s" % (filepath.replace("%sapps/%s/%s/" % (config.basemap, app, version), ""))
					self.writeFile(filepath, name)
	
	def closeAndGetName(self):
		self.zipFile.close()