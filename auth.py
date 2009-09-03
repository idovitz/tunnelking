#!/usr/bin/python

import sys, os, config, ldap, string, smtplib, time
from random import choice

sys.path.append("%s/lib" % os.path.abspath(sys.path[0]))
from tunnelking.Log import Log
from tunnelking.DBmysql import *
from tunnelking.Sms import *

log = Log(config.logging, "auth.py")
log.log(3, "ldapauth started for user %s" % os.environ["username"])
log.log(3, "environ %s" % os.environ)

userid = None

def main():
	global userid
	
	domain = os.environ["tls_id_0"][os.environ["tls_id_0"].find("users.")+6:os.environ["tls_id_0"].find('/', 2)]
	
	# check serial
	if not checkSerial():
		log.log(3, "exit checkSerial")
		sys.exit(1)
	
	# checks if commonname cert == username 
	if not checkCommonName():
		log.log(3, "exit checkCommonName")
		sys.exit(1)
	
	if getAuthType(domain) == "LDAP":
		if checkLdap():
			if sendKey(domain, os.environ["username"], os.environ["untrusted_ip"]):
				log.log(3, "exit sendKey")
				sys.exit(1)
			else:
				logLastLogin(userid)
				sys.exit(0)
	else:
		if checkLocal(domain):
			if sendKey(domain, os.environ["username"], os.environ["untrusted_ip"]):
				log.log(3, "exit sendKey")
				sys.exit(1)
			else:
				logLastLogin(userid)
				sys.exit(0)
				
	if checkKey(os.environ["username"], os.environ["password"], domain, os.environ["untrusted_ip"]):
		logLastLogin(userid)
		sys.exit(0)
	else:
		sys.exit(1)
		
def checkSerial():
	sn = os.environ["tls_id_0"][os.environ["tls_id_0"].find("SN=")+3:]
	cn = os.environ["tls_id_0"][os.environ["tls_id_0"].find("CN=")+3:os.environ["tls_id_0"].find('/', 2)]
	
	try:
		db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
		sql = "SELECT cn, serial FROM `ssl` WHERE cn = '%s' AND serial = '%s'" % (cn, sn)
		log.log(3, sql)
		
		result = db.querySQL(sql)
		log.log(3, sql)
		if len(result):
			return True
		else:
			return False
	except Exception, e:
		log.log(2, "%s: %s" % (type(e), e))
		sys.exit(1)

def checkCommonName():
	if "%s.users" % os.environ["username"] in os.environ["tls_id_0"]:
		log.log(3, "%s contains %s" % (os.environ["tls_id_0"], os.environ["username"]))
		return True
	else:
		log.log(3, "%s contains not %s" % (os.environ["tls_id_0"], os.environ["username"]))
		return False

def getAuthType(domain):
	try:
		db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
		sql = "SELECT co.*, opt.value AS ldap FROM configurations AS co JOIN options AS opt ON co.id = opt.confid WHERE co.dn = '%s' AND opt.name = 'ldap'" % (domain)
		result = db.querySQL(sql)
		log.log(3, "%s" % result[0]["ldap"])
		if result[0]["ldap"] == "True":
			return "LDAP"
		else:
			return "LOCAL"
	except Exception, e:
		log.log(2, "%s: %s" % (type(e), e))
		sys.exit(1)
	
	
def checkLocal(domain):
	log.log(3, "local check")
	
	try:
		log.log(2, "started for dn %s and username %s" % (os.environ["tls_id_0"], os.environ["username"]))
		
		db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
		sql = "SELECT us.name FROM users AS us JOIN configurations AS co ON us.confid = co.id WHERE us.name = '%s' AND us.password = SHA1('%s') AND co.dn = '%s'" % (os.environ["username"], os.environ["password"], domain)
		result = db.querySQL(sql)
		log.log(3, sql)
		log.log(3, "result length %s " % len(result))
		
		if len(result):
			return True
		else:
			return False
	except Exception, e:
		log.log(2, "%s: %s" % (type(e), e))
		sys.exit(1)

def checkLdap():
	log.log(3, "ldap check")
	
	ip, dn = sys.argv[1:3]
	
	if os.environ["password"] != "":
		try:
			con = ldap.open(ip)
			log.log(3, "check user %s" % os.environ["username"])
			con.simple_bind_s("%s@%s" % (os.environ["username"], dn), os.environ["password"])
			log.log(3, "bind succesfull user %s" % os.environ["username"])
			return True
		except ldap.INVALID_CREDENTIALS:
			log.log(2, "ldap logon failed")
			return False
		except Exception, e:
			log.log(2, "%s: %s" % (type(e), e))
			sys.exit(1)
	else:
		return False

def sendKey(domain, username, ip):
	global userid
	log.log(2, "sendkey")
	
	key = ""
	for i in range(8):
		key += choice(string.letters+string.digits)
	
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
		userid = result[0]["id"]
	
	if result[0]["otpRecipient"] != "":
		try:
			# send key
			msg = "%s geldig vanaf %s geldig tot %s" % (key, ip, time.strftime("%d-%m-%Y %H:%M", time.localtime(time.time()+(60*60*12))))
			print msg
			sms = Sms(config.smsHandler, config.smsOptions)
			res = sms.send(result[0]["otpRecipient"], msg)
		
			# delete old keys for ip / user
			db.execSQL("DELETE FROM `keys` WHERE `userid` = '%s' AND ip = '%s'" % (result[0]["id"], ip))
			
			# insert session key
			sql = "INSERT INTO `keys` (`userid`, `key`, `expiretime`, `ip`) VALUES(%s, '%s', DATE_ADD(NOW(), INTERVAL 12 HOUR), '%s')" % (result[0]["id"], key, ip)
			log.log(3, "sql: %s" % (sql))
			db.execSQL(sql)
			log.log(2, "%s sended: %s" % (key, res))
			return True
		except Exception, e:
			log.log(2, "%s: %s" % (type(e), e))
			sys.exit(1)
	else:
		log.log(2, "NO OTP for %s" % username)
		return False

def checkKey(username, key, domain, ip):
	global userid
	log.log(3, "checkkey")
	
	# remove old keys
	try:
		db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
		db.execSQL("DELETE FROM `keys` WHERE `expiretime` < NOW()")
	except Exception, e:
		log.log(2, "%s: %s" % (type(e), e))
		sys.exit(1)
	
	try:
		sql = "SELECT us.id, us.otpRecipient FROM users AS us JOIN configurations AS co ON us.confid = co.id WHERE us.name = '%s' AND co.dn = '%s'" % (username, domain)
		result = db.querySQL(sql)
		log.log(3, "sql: %s" % (sql))
		log.log(3, "sql: %s" % (len(result)))
		
		if len(result):
			userid = result[0]["id"]
			sql = "SELECT * FROM `keys` WHERE `userid` = %s AND `key` = '%s' AND `expiretime` > NOW() AND ip = '%s'" % (result[0]["id"], key, ip)
			log.log(3, "sql: %s" % (sql))
			result = db.querySQL(sql)
			if len(result):
				return True
			else:
				return False
		else:
			return False
	except Exception, e:
		log.log(2, "%s: %s" % (type(e), e))
		sys.exit(1)

def logLastLogin(id):
	# insert session key
	try:
		db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
		sql = "UPDATE users SET lastlogin = NOW() WHERE id = %s" % id
		db.execSQL(sql)
	except Exception, e:
		log.log(2, "%s: %s" % (type(e), e))
		sys.exit(1)
	
if __name__ == '__main__':
    main()