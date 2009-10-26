
import config, os, signal, cherrypy
from subprocess import Popen
from ConnectionManager import *
from CertificateHelper import *
from LdapHandler import *
from ncrypt import *
from DBmysql import *

class Configuration(object):
	def __init__(self, id, name, dn):
		self.id = id
		self.name = name
		self.dn = dn
		self.options = {}
		self.data = {}
		self.push = []
				
		self.db = cherrypy.thread_data.db
			
	def __setitem__(self, key, item):
		self.data[key] = item
		
	def __getitem__(self, key):
		return self.data[key]
		
	def load(self):
		self.getOptions()
		self.getData()
		self.getPushOptions()
		self.ch = CertificateHelper(self.id)
		self.ch.load()
		
	def initConnectionManager(self):
		self.connectionManager = ConnectionManager("127.0.0.1", self.options["management"][1])
	
	def new(self, formdata):
		# DEFAULT OPTIONS
		self.options = { 'daemon': [''],
						 'user': ['nobody'],
						 'persist-key': [''],
						 'management': ['127.0.0.1', formdata["manport"]],
						 'group': ['nogroup'],
						 'tls-auth': ['ssl/keys/ta.%s.key' % formdata["domain"], '0'],
						 'dh': ['ssl/dh1024.pem'],
						 'proto': [formdata["protocol"]],
						 'ca': ['ssl/certs/ca.%s.cert' % formdata["domain"]],
						 'dev': ['tun'],
						 'server': [formdata["pool"], formdata["netmask"]],
						 'persist-tun': [''],
						 'cert': ['ssl/certs/server.%s.cert' % formdata["domain"]],
						 'verb': ['3'],
						 'mode': ['server'],
						 'key': ['ssl/keys/server.%s.key' % formdata["domain"]],
						 'ping': ['5'],
						 'ping-restart': ['20'],
						 'reneg-sec': ['0'],
						 'port': [formdata["port"]],
						 'writepid': ['tmp/%s.pid' % self.name],
						 'tls-server': [''],
						 'persist-local-ip': [''],
						 'persist-remote-ip': [''],
						 'duplicate-cn': [''],
						 'username-as-common-name': [''],
						 'comp-lzo': [''],
						 #"script-security": ['3'],
						 "topology": ['subnet']
						 }		
		
		self.data["remoteip"] = formdata["remoteip"]
		self.data["domain"] = formdata["domain"]
		self.data["o"] = formdata["o"]
		self.data["ou"] = formdata["ou"]
		self.data["c"] = formdata["c"]
		self.data["st"] = formdata["st"]
		self.data["l"] = formdata["l"]
		self.data["ldap"] = len(formdata["ldapDict"]) > 0
		
		if self.data["ldap"]:
			self.data.update(formdata["ldapDict"])
		
		self.db.execSQL("INSERT INTO configurations (name, dn) VALUES('%s', '%s')" % (self.name, formdata["domain"]));
		self.id = int(self.db.cursor.lastrowid)
		self.db.newCursor()
		
		self.ch = CertificateHelper(self.id)
		self.ch.createCA("ca.%s" % formdata["domain"], formdata["o"], formdata["ou"], formdata["c"], formdata["st"], formdata["l"])
		self.ch.createKey("server.%s" % formdata["domain"], formdata["o"], formdata["ou"], formdata["c"], formdata["st"], formdata["l"])
		self.ch.createTLSKey("ta.%s" % formdata["domain"])
		
		self.dn = formdata["domain"]
		
		self.savePushOptions(["ping 5", "ping-restart 20", "explicit-exit-notify"])
		self.saveOptions()
		self.saveData()
		
	def saveLdap(self, ip, dn, sf, bd, bp):
		try:
			self.db.execSQL("UPDATE configurations SET ldap = 1, ldap_server = '%s', ldap_user = '%s', ldap_pass = '%s', ldap_basedn = '%s', ldap_filter = '%s'" % (ip, bd, bp, dn, sf));
			self.db.newCursor()
			return True
		except:
			return False
		
	def savePushOptions(self, options):
		try:
			self.db.execSQL("DELETE FROM options WHERE confid = %s AND type = 'p'" % self.id)
			self.db.newCursor()
			self.push = options
			for option in options:
				self.db.execSQL("INSERT INTO options (confid, type, name, value) VALUES(%s, 'p', 'push', '%s')" % (self.id, option));
				self.db.newCursor()
			return True
		except Exception, e:
			print "%s: %s" % (type(e), e)
			return False
	
	def getPushOptions(self):
		optionsResult = self.db.querySQL("SELECT value FROM options WHERE confid = %s AND type = 'p' ORDER BY id" % self.id)
		self.db.newCursor()
		
		for opt in optionsResult:
			self.push.append(opt["value"])
		
	def delete(self):
		self.stop()
		self.db.execSQL("DELETE FROM configurations WHERE id = %s" % self.id)
		self.db.execSQL("DELETE FROM options WHERE confid = %s" % self.id)
		self.db.execSQL("DELETE FROM users WHERE confid = %s" % self.id)
		self.db.execSQL("DELETE FROM `ssl` WHERE confid = %s" % self.id)
		self.db.newCursor()
		
	def getOptions(self):
		self.options = {}
		
		optionsResult = self.db.querySQL("SELECT * FROM options WHERE confid = %s AND type = 'o' ORDER BY id" % self.id)
		self.db.newCursor()
		for opt in optionsResult:
			if not self.options.has_key(opt['name']):
				self.options[opt['name']] = [opt['value']]
			else:
				self.options[opt['name']].append(opt['value'])
		
	def getData(self):
		self.data = {}
		
		dataResult = self.db.querySQL("SELECT * FROM options WHERE confid = %s AND type = 'd' ORDER BY id" % self.id)
		self.db.newCursor()
		
		for data in dataResult:
			self.data[data["name"]] = data["value"]
			
		if self.data["ldap"] == "True" or self.data["ldap"] == True:
			self.lh = LdapHandler(self.data["ldap_ip"], self.data["ldap_dn"], self.data["ldap_sf"], self.data["ldap_bd"], self.data["ldap_bp"])
		
	def saveOptions(self):
		for key, values in self.options.iteritems():
			for value in values:
				self.db.execSQL("INSERT INTO options (confid, type, name, value) VALUES(%s, 'o', '%s', '%s')" % (self.id, key, value));
		self.db.newCursor()
	
	def saveData(self):
		for key, value in self.data.iteritems():
			self.db.execSQL("INSERT INTO options (confid, type, name, value) VALUES(%s, 'd', '%s', '%s')" % (self.id, key, value));
		self.db.newCursor()	
	
	def writeConfigFile(self):
		f = open("conf/%s.conf" % self.name, "w")
		wlist = []
		
		for key, values in self.options.iteritems():
			line = key
			for value in values:
				line = line + " " + value
			
			line = line + "\n"
			wlist.append(line)
		
		f.writelines(wlist)
		f.close
		
	
	def readConfigFile(self):
		# parse configuration
		f = open("conf/%s.conf" % self.name, "r")
		lines = f.readlines()
		
		for line in lines:
			if line.strip() != "" and line[0] != "#":
				spline = line.strip().split(" ")
				optionName = spline[0]
				spline.remove(optionName)
				self.options[optionName] = spline
	
#	def loadSSL(self):
#		# load CA Key
#		self.caKey = rsa.RSAKey()
#		self.caKey.fromPEM_PrivateKey(file(self.options['ca'][0]).read(), "t3r1ng")
#		
#		# load CA cert
#		self.caCert = x509.X509Certificate()
#		self.caCert.fromPEM(file(self.options['ca'][0]).read())
	
	def getPid(self):
		f = open("tmp/%s.pid" % self.name, "r")
		return f.read().strip()
	
	def running(self):
		if os.path.exists("tmp/%s.pid" % self.name):
			return os.path.exists("/proc/%s" % self.getPid())
		else:
			return False
	
	def getStatus(self):
		connections = {}
		
		if self.running() == True:
			try:
				cm = self.connectionManager
			except:
				self.initConnectionManager()
		
			self.connectionManager.connect()
			connections = self.connectionManager.getConnections()
			self.connectionManager.close()
		
		return {'running': self.running(), 'connections': connections}
	
	def createLdapConf(self):
		str = "<LDAP>\n"
		str = str+"\tURL \"ldap://%s\"\n" % self.data["ldap_ip"]
		str = str+"\tBindDN \"%s\"\n" % self.data["ldap_bd"]
		str = str+"\tPassword \"%s\"\n" % self.data["ldap_bp"]
		str = str+"\tTimeout 15\n"
		str = str+"</LDAP>\n"
		str = str+"<Authorization>\n"
		str = str+"\tBaseDN \"%s\"\n" % self.data["ldap_dn"]
		str = str+"\tSearchFilter \"%s\"\n" % self.data["ldap_sf"]
		str = str+"\tRequireGroup false\n"
		str = str+"</Authorization>\n"
		
		f = open("conf/ldap_%s.conf" % self.name, "w")
		f.write(str)
		f.close()
	
	def start(self):
		if not self.running():
			args = ""
			
			# write certificates
			self.ch.writeTmp()
			
			# add auth
			if self.data["ldap"] == "True" or self.data["ldap"] == True:
				args = args+' --auth-user-pass-verify \"<basemap>auth.py %s %s\" via-env' % (self.data["ldap_ip"], self.dn)
			else:
				args = args+" --auth-user-pass-verify \"<basemap>auth.py\" via-env"
				
			args = args+" --learn-address \"<basemap>learnaddress.py %s\"" % (self.dn)
			
			for key, values in self.options.iteritems():
				arg = "--"+key
				for value in values:
					arg = arg + " " + value
				
				args = args+" "+arg
			
			for pushOption in self.push:
				 arg = "--push '%s'" % pushOption
				 args = args+" "+arg
				 
			args = args.replace("<basemap>", config.basemap)
			
			print "/usr/bin/sudo /usr/sbin/openvpn"+args
			p = Popen("/usr/bin/sudo /usr/sbin/openvpn"+args, shell=True, close_fds=True)
		
		return self.running()
	
	def restart(self):
		self.stop()
		time.sleep(1)
		self.start()
		
	def stop(self):
		if self.running() == True:
			try:
				Popen("/usr/bin/sudo /usr/bin/stop.py %s" % self.getPid(), shell=True, close_fds=True)
			except Exception, e:
				print e
				return False
			
			time.sleep(0.5)
			
			if self.running() == False:
				# remove certs and keys
				for dir in os.walk("ssl"):
					for file in dir[2]:
						if self.dn in file:
							os.remove("%s/%s" % (dir[0], file))
				
				# remove tmp files
				for dir in os.walk("tmp"):
					for file in dir[2]:
						if self.dn in file:
							os.remove("%s/%s" % (dir[0], file))
							
				# remove pid
				if os.path.exists("tmp/%s.pid" % self.name):
					os.remove("tmp/%s.pid" % self.name)
		
		return not self.running()