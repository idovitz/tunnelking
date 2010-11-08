#!/usr/bin/python

import sys, os, config, string, time, random, traceback

sys.path.append("%s/lib" % os.path.abspath(sys.path[0]))
from tunnelking.Log import Log
from tunnelking.DBmysql import *
from tunnelking.Sms import *
from tunnelking.OtpKey import *

log = Log(config.logging, "learnaddress.py")
log.log(3, "learnaddress started for user %s" % sys.argv[3])

class LearnAddress:
	def main(self):
		self.userid = 0
		
		try:
			if len(sys.argv) == 5:
				domain, learntype, ip, username = sys.argv[1:5]
			else:
				domain, learntype, ip = sys.argv[1:4]
			
			if learntype == "add" or learntype == "update":
				if self.checkOTP(username, domain):
					user = self.getUser(username, domain)
					
					cc = self.checkConnection(ip, os.environ['trusted_ip'])
					log.log(3, "cc: %s" % cc)
					
					if cc == 1:
						log.log(3, "trusted connection in keys")
						self.freeIP(ip, user['id'])
					elif cc == 0:
						self.quarantaineIP(ip, user['id'])
						self.sendKey(domain, username, ip)
						log.log(3, "no connections found, key sended")
					elif cc == 2:
						log.log(3, "untrusted connection found")
						self.quarantaineIP(ip, user['id'])
				else:
					self.freeIP(ip, user['id'])
			elif learntype == "delete":
				self.quarantaineIP(ip, 0)
			
			self.learn(os.environ['trusted_ip'], ip, self.userid)
			log.log(3, "connection inserted")
			
		except Exception, e:
			log.log(2, "mainTry %s: %s" % (type(e), e))
			traceback.print_exc()
			sys.exit(1)
	
		sys.exit(0)
	
	def learn(self, rip, lip, id):
		try:
			db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
			
			sql = "INSERT INTO connections (lip, rip, userid) VALUES('%s', '%s', %s) ON DUPLICATE KEY UPDATE rip = '%s', userid = %s" % (lip, rip, id, rip, id)
			log.log(3, "sql: %s" % (sql))
			
			db.execSQL(sql)
		except Exception, e:
			log.log(2, "learn %s: %s" % (type(e), e))
			sys.exit(1)
		
	def quarantaineIP(self, ip, id):
		log.log(3, "quarantaine %s" % ip)
		f = os.system("/usr/bin/sudo /usr/bin/qip.py delete %s %s" % (ip, id))
		log.log(3, "/usr/bin/sudo /usr/bin/qip.py delete %s %s: %s" % (ip, id, f))
	
	def freeIP(self, ip, id):
		log.log(3, "free %s" % ip)
		f = os.system("/usr/bin/sudo /usr/bin/qip.py add %s %s" % (ip, id))
		log.log(3, "/usr/bin/sudo /usr/bin/qip.py add %s %s: %s" % (ip, id, f))
	
	def checkOTP(self, username, domain):
		try:
			db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
			
			sql = "SELECT us.id, us.otpRecipient FROM users AS us JOIN configurations AS co ON us.confid = co.id WHERE us.name = '%s' AND co.dn = '%s'" % (username, domain)
			log.log(3, "sql: %s" % (sql))
			
			result = db.querySQL(sql)
			log.log(3, "res: %s" % (result))
		except Exception, e:
			log.log(2, "%s: %s" % (type(e), e))
			sys.exit(1)
			
		if len(result) != 0:
			self.userid = result[0]["id"]
		
		if result[0]["otpRecipient"] != "":
			return True
		else:
			return False
	
	def checkConnection(self, lip, rip):
		try:
			db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
			
			sql = "SELECT `trusted` FROM `keys` WHERE rip = '%s' AND userid = %s AND `expiretime` > NOW() ORDER BY expiretime DESC LIMIT 1" % (rip, self.userid)
			log.log(3, "sql: %s" % (sql))
			
			result = db.querySQL(sql)
		except Exception, e:
			log.log(2, "%s: %s" % (type(e), e))
			sys.exit(1)
			
		if len(result) != 0:
			log.log(3, "res: %s" % (str(result)))
			if result[0]['trusted'] == 1:
				return 1
			else:
				return 2
		else:
			return 0
	
	def sendKey(self, domain, username, ip):
		key = OtpKey(config, log)
		key.sendKey(self.getUser(username, domain), ip, os.environ['trusted_ip'])
		
	def getUser(self, username, domain):
		try:
			db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
			
			sql = "SELECT us.id, us.otpRecipient, us.name FROM users AS us JOIN configurations AS co ON us.confid = co.id WHERE us.name = '%s' AND co.dn = '%s'" % (username, domain)
			log.log(3, "sql: %s" % (sql))
			
			result = db.querySQL(sql)
			log.log(3, "res: %s" % (result))
		except Exception, e:
			log.log(2, "GETUSER %s: %s" % (type(e), e))
			sys.exit(1)
			
		if len(result) != 0:
			return result[0]
		else:
			return 0

if __name__ == '__main__':
	la = LearnAddress()
	la.main()