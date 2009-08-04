
import config, os, signal
from subprocess import Popen
from ConnectionManager import *
from CertificateHelper import *
from ncrypt import *
from DBmysql import *

class Configuration(object):
	def __init__(self, id, name, dn):
		self.id = id
		self.name = name
		self.dn = dn
		self.options = {}
		self.data = {}
				
		self.db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
			
	def __setitem__(self, key, item):
		self.data[key] = item
		
	def __getitem__(self, key):
		return self.data[key]
		
	def load(self):
		self.getOptions()
		self.ch = CertificateHelper(self.id)
		self.ch.load()
		
	def initConnectionManager(self):
		self.connectionManager = ConnectionManager("127.0.0.1", self.options["management"][1])
	
	def new(self, domain, o, ou, c, st, l, ports):
		# DEFAULT OPTIONS
		self.options = { 'daemon': [''],
						 'user': ['nobody'],
						 'persist-key': [],
						 'management': ['127.0.0.1', ports[1]],
						 'group': ['nogroup'],
						 'tls-auth': ['ssl/ta.key', '0'],
						 'dh': ['ssl/dh1024.pem'],
						 'proto': [ports[2]],
						 'ca': ['ssl/certs/ca.%s.cert' % domain],
						 'dev': ['tun'],
						 'server': ['192.168.123.0', '255.255.255.0'],
						 'persist-tun': [],
						 'cert': ['ssl/certs/server.%s.cert' % domain],
						 'verb': ['3'],
						 'mode': ['server'],
						 'key': ['ssl/keys/server.%s.key' % domain],
						 'keepalive': ['10', '60'],
						 'port': [ports[0]],
						 'writepid': ['tmp/%s.pid' % self.name],
						 'tls-server': [''],
						 'persist-tun': [''],
						 'persist-key': ['']}
		
		self.db.execSQL("INSERT INTO configurations (name, dn) VALUES('%s', '%s')" % (self.name, domain));
		self.id = self.db.cursor.lastrowid
		
		self.ch = CertificateHelper(self.id)
		self.ch.createCA("ca.%s" % domain, o, ou, c, st, l)
		self.ch.createKey("server.%s" % domain, o, ou, c, st, l)
		
		self.dn = domain
		
		self.saveOptions()
		
	def saveLdap(self, ip, dn, sf, bd, bp):
		try:
			self.db.execSQL("UPDATE configurations SET ldap = 1, ldap_server = '%s', ldap_user = '%s', ldap_pass = '%s', ldap_basedn = '%s', ldap_filter = '%s'" % (ip, bd, bp, dn, sf));
			return True
		except:
			return False
		
	def delete(self):
		self.stop()
		self.db.execSQL("DELETE FROM configurations WHERE id = %s" % self.id)
		self.db.execSQL("DELETE FROM options WHERE confid = %s" % self.id)
		self.db.execSQL("DELETE FROM users WHERE confid = %s" % self.id)
		self.db.execSQL("DELETE FROM `ssl` WHERE confid = %s" % self.id)
		
	def getOptions(self):
		self.options = {}
		
		optionsResult = self.db.querySQL("SELECT * FROM options WHERE confid = %s ORDER BY id" % self.id)
		for opt in optionsResult:
			if not self.options.has_key(opt['name']):
				self.options[opt['name']] = [opt['value']]
			else:
				self.options[opt['name']].append(opt['value'])
		
	def saveOptions(self):
		for key, values in self.options.iteritems():
			for value in values:
				self.db.execSQL("INSERT INTO options (confid, name, value) VALUES(%s, '%s', '%s')" % (self.id, key, value));
	
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
	
	def loadSSL(self):
		# load CA Key
		self.caKey = rsa.RSAKey()
		self.caKey.fromPEM_PrivateKey(file(self.options['ca'][0]).read(), "t3r1ng")
		
		# load CA cert
		self.caCert = x509.X509Certificate()
		self.caCert.fromPEM(file(self.options['ca'][0]).read())
	
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
	
	def start(self):
		if not self.running():
			args = ""
			self.ch.writeTmp()
			
			for key, values in self.options.iteritems():
				arg = "--"+key
				for value in values:
					arg = arg + " " + value
				
				args = args+" "+arg
			
			print "/usr/bin/sudo /usr/sbin/openvpn"+args
			p = Popen("/usr/bin/sudo /usr/sbin/openvpn"+args, shell=True, close_fds=True)
		
		return self.running()
	
	def restart(self):
		self.stop()
		self.start()
		
	def stop(self):
		if self.running() == True:
			try:
				Popen("/usr/bin/sudo /usr/bin/stop.py %s" % self.getPid(), shell=True, close_fds=True)
			except Exception, e:
				print e
				return False
		
		return not self.running()