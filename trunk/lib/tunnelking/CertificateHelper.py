
import time, sys, config, re
from ncrypt import *
from DBmysql import *

class CertificateHelper:
	def __init__(self, confid):
		self.db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
		self.confid = confid
		self.certs = {}
		self.keys = {}
			
	def load(self):
		self.certs = {}
		self.keys = {}
		
		res = self.db.querySQL("SELECT * FROM `ssl` WHERE confid = %s" % self.confid)
		
		for entry in res:
			if entry["type"] == 'cakey':
				self.caKey = rsa.RSAKey()
				self.caKey.fromPEM_PrivateKey(entry["pem"])
			elif entry["type"] == 'cacert':
				self.caCert = x509.X509Certificate()
				self.caCert.fromPEM(entry["pem"])
			elif entry["type"] == 'cert':
				self.certs[entry["cn"]] = x509.X509Certificate()
				self.certs[entry["cn"]].fromPEM(entry["pem"])
			elif entry["type"] == 'key':
				self.keys[entry["cn"]] = rsa.RSAKey()
				self.keys[entry["cn"]].fromPEM_PrivateKey(entry["pem"])
	
	def writeTmp(self):
		for cn,key in self.keys.iteritems():
			print cn
			if "server" in cn:
				f = open("ssl/keys/%s.key" % cn, "w")
				f.write(key.toPEM_PrivateKey())
		for cn,cert in self.certs.iteritems():
			print cn
			if "server" in cn:
				f = open("ssl/certs/%s.cert" % cn, "w")
				f.write(cert.toPEM())
		
		cn = self.caCert.getIssuer().lookupEntry("commonName")
		f = open("ssl/certs/%s.cert" % cn, "w")
		f.write(self.caCert.toPEM())
		
	def createCA(self, cn, o, ou, c, st, l):
		# key
		self.caKey = rsa.RSAKey()
		self.caKey.generate(2048)
		
		# certificate
		self.caCert = x509.X509Certificate()
		xn = x509.X509Name()
		xn.addEntry('CN', cn)
		xn.addEntry('O', o)
		xn.addEntry('OU', ou)
		xn.addEntry('C', c)
		xn.addEntry('ST', st)
		xn.addEntry('L', l)
		self.caCert.setVersion(3)
		self.caCert.setSerialNumber(1)
		self.caCert.setSubject(xn)
		self.caCert.setIssuer(xn)
		self.caCert.setPublicKey(self.caKey)
		self.caCert.setNotBefore(0)
		self.caCert.setNotAfter(int(time.time()) + 365*24*60*60*10)
		self.caCert.sign(self.caKey, digest.DigestType('sha1'))
		
		self.db.execSQL("""INSERT INTO `tunnelking`.`ssl` (`cn`, `confid`, `type`, `pem`) VALUES('%s', %s, 'cakey', '%s')""" % (cn, self.confid, self.caKey.toPEM_PrivateKey()))
		self.db.execSQL("""INSERT INTO `tunnelking`.`ssl` (`cn`, `confid`, `type`, `pem`) VALUES('%s', %s, 'cacert', '%s')""" % (cn, self.confid, self.caCert.toPEM()))
	
	def createKey(self, cn, o, ou, c, st, l):
		# generate new key
		self.keys[cn] = rsa.RSAKey()
		self.keys[cn].generate(2048)
		
		# generate cert and sign
		self.certs[cn] = x509.X509Certificate()
		xn = x509.X509Name()
		xn.addEntry('CN', cn)
		xn.addEntry('O', o)
		xn.addEntry('OU', ou)
		xn.addEntry('C', c)
		xn.addEntry('ST', st)
		xn.addEntry('L', l)
		self.certs[cn].setVersion(3)
		self.certs[cn].setSerialNumber(1)
		self.certs[cn].setSubject(xn)
		self.certs[cn].setIssuer(self.caCert.getIssuer())
		self.certs[cn].setPublicKey(self.keys[cn])
		self.certs[cn].setNotBefore(0)
		self.certs[cn].setNotAfter(int(time.time()) + 365*24*60*60*3)
		self.certs[cn].sign(self.caKey, digest.DigestType('sha1'))
		
		self.db.execSQL("""INSERT INTO `tunnelking`.`ssl` (`cn`, `confid`, `type`, `pem`) VALUES('%s', %s, 'key', '%s')""" % (cn, self.confid, self.keys[cn].toPEM_PrivateKey()))
		self.db.execSQL("""INSERT INTO `tunnelking`.`ssl` (`cn`, `confid`, `type`, `pem`) VALUES('%s', %s, 'cert', '%s')""" % (cn, self.confid, self.certs[cn].toPEM()))
		
	def createUserKey(self, cn):
		# generate new key
		self.keys[cn] = rsa.RSAKey()
		self.keys[cn].generate(2048)
		
		# generate cert and sign
		self.certs[cn] = x509.X509Certificate()
		xn = self.caCert.getIssuer()
		xn.addEntry('CN', cn)
#		xn.addEntry('O', o)
#		xn.addEntry('OU', ou)
#		xn.addEntry('C', c)
#		xn.addEntry('ST', st)
#		xn.addEntry('L', l)
		self.certs[cn].setVersion(3)
		self.certs[cn].setSerialNumber(1)
		self.certs[cn].setSubject(xn)
		self.certs[cn].setIssuer(self.caCert.getIssuer())
		self.certs[cn].setPublicKey(self.keys[cn])
		self.certs[cn].setNotBefore(0)
		self.certs[cn].setNotAfter(int(time.time()) + 365*24*60*60)
		self.certs[cn].sign(self.caKey, digest.DigestType('sha1'))
		
		self.db.execSQL("""INSERT INTO `tunnelking`.`ssl` (`cn`, `confid`, `type`, `pem`) VALUES('%s', %s, 'key', '%s')""" % (cn, self.confid, self.keys[cn].toPEM_PrivateKey()))
		self.db.execSQL("""INSERT INTO `tunnelking`.`ssl` (`cn`, `confid`, `type`, `pem`) VALUES('%s', %s, 'cert', '%s')""" % (cn, self.confid, self.certs[cn].toPEM()))
		
	def delUserKey(self, cn):
		self.keys[cn] = None
		self.certs[cn] = None
		
		self.db.execSQL("DELETE FROM `ssl` WHERE cn = '%s' AND confid = %s" % (cn, self.confid))
		
	def getUserKey(self, cn, pin):
		
		return {'%s.key' % cn:self.keys[cn].toPEM_PrivateKey(pin), '%s.cert' % cn: self.certs[cn].toPEM()}