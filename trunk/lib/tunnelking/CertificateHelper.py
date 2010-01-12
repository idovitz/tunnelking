
import os, time, sys, config, re, hashlib, cherrypy
from ncrypt import *
from DBmysql import *
from subprocess import Popen

class CertificateHelper:
	def __init__(self, confid):
		self.db = cherrypy.thread_data.db
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
			elif entry["type"] == 'tls':
				self.tlskey = [entry["cn"], entry["pem"]]
	
	def writeTmp(self):
		for cn,key in self.keys.iteritems():
			if "server" in cn:
				f = open("ssl/keys/%s.key" % cn, "w")
				f.write(key.toPEM_PrivateKey())
				f.close()
		for cn,cert in self.certs.iteritems():
			if "server" in cn:
				f = open("ssl/certs/%s.cert" % cn, "w")
				f.write(cert.toPEM())
				f.close()
		
		# TLS key
		f = open("ssl/keys/%s.key" % self.tlskey[0], "w")
		f.write(self.tlskey[1])
		f.close()
		
		# CA cert
		cn = self.caCert.getIssuer().lookupEntry("commonName")
		f = open("ssl/certs/%s.cert" % cn, "w")
		f.write(self.caCert.toPEM())
		f.close()
		
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
		self.certs[cn].setNotAfter(int(time.time()) + 365*24*60*60*5)
		self.certs[cn].sign(self.caKey, digest.DigestType('sha1'))
		
		self.db.execSQL("""INSERT INTO `tunnelking`.`ssl` (`cn`, `confid`, `type`, `pem`) VALUES('%s', %s, 'key', '%s')""" % (cn, self.confid, self.keys[cn].toPEM_PrivateKey()))
		self.db.execSQL("""INSERT INTO `tunnelking`.`ssl` (`cn`, `confid`, `type`, `pem`) VALUES('%s', %s, 'cert', '%s')""" % (cn, self.confid, self.certs[cn].toPEM()))
	
	def createTLSKey(self, cn):
		Popen("/usr/sbin/openvpn --genkey --secret ssl/%s.key" % cn, shell=True, close_fds=True)
		time.sleep(1)
		f = open("ssl/%s.key" % cn, "r")
		self.tlskey = [cn, f.read()]
		f.close()
		
		os.remove("ssl/%s.key" % cn)
		
		self.db.execSQL("""INSERT INTO `tunnelking`.`ssl` (`cn`, `confid`, `type`, `pem`) VALUES('%s', %s, 'tls', '%s')""" % (cn, self.confid, self.tlskey[1]))
	
	def createUserKey(self, cn):
		# generate new key
		self.keys[cn] = rsa.RSAKey()
		self.keys[cn].generate(2048)
		
		# generate cert and sign
		self.certs[cn] = x509.X509Certificate()
		xn = x509.X509Name()
		xn.addEntry('CN', cn)
		ts = hashlib.sha256("%s_%s" % (time.localtime(), cn)).hexdigest()
		xn.addEntry('SN', ts)
		self.certs[cn].setVersion(3)
		self.certs[cn].setSerialNumber(1)
		self.certs[cn].setSubject(xn)
		self.certs[cn].setIssuer(self.caCert.getIssuer())
		self.certs[cn].setPublicKey(self.keys[cn])
		self.certs[cn].setNotBefore(0)
		self.certs[cn].setNotAfter(int(time.time()) + 365*24*60*60*3)
		self.certs[cn].sign(self.caKey, digest.DigestType('sha1'))
		
		self.db.execSQL("""INSERT INTO `tunnelking`.`ssl` (`cn`, `confid`, `type`, `pem`) VALUES('%s', %s, 'key', '%s')""" % (cn, self.confid, self.keys[cn].toPEM_PrivateKey()))
		self.db.execSQL("""INSERT INTO `tunnelking`.`ssl` (`cn`, `confid`, `type`, `pem`, `serial`) VALUES('%s', %s, 'cert', '%s', '%s')""" % (cn, self.confid, self.certs[cn].toPEM(), ts))
		
	def delUserKey(self, cn):
		self.keys[cn] = None
		self.certs[cn] = None
		
		self.db.execSQL("DELETE FROM `ssl` WHERE cn = '%s' AND confid = %s" % (cn, self.confid))
		
	def getExpireDate(self, username, dn, pin):
		ucn = '%s.users.%s' % (username, dn)
		
		return self.certs[ucn].getNotAfter()
		
	def getUserKey(self, username, dn, pin):
		ucn = '%s.users.%s' % (username, dn)
		
		if pin != "":
			key = self.keys[ucn].toPEM_PrivateKey(pin)
		else:
			key = self.keys[ucn].toPEM_PrivateKey()
			
		return {'%s.key' % ucn:key, '%s.cert' % ucn: self.certs[ucn].toPEM(), "ca.%s.cert" % dn:self.caCert.toPEM(), "%s.key" % self.tlskey[0]:self.tlskey[1]}