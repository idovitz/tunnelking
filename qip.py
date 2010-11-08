#!/usr/bin/python

import sys, os, config, time, qip_rules

sys.path.append("%s/lib" % os.path.abspath(sys.path[0]))
from tunnelking.Log import Log
from tunnelking.DBmysql import *
from tunnelking import Chain, Rule

log = Log(config.logging, "qip.py")
log.log(3, "qip started for ip %s" % sys.argv[2])
log.log(3, "args %s" % sys.argv)

try:
	action, ip, id = sys.argv[1:4]
except:
	sys.exit(1)


def getUserApps(id):
	try:
		db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
		
		sql = "SELECT ap.appname FROM apps_users ap WHERE ap.userid = %s" % id
		log.log(3, "sql: %s" % (sql))
		
		result = db.querySQL(sql)
#		log.log(3, "res: %s" % (result))
	except Exception, e:
		log.log(3, "%s: %s" % (type(e), e))
		sys.exit(1)
		
	if len(result) != 0:
		return result
	else:
		return 0

def getUser(id):
		try:
			db = DBmysql(config.databaseUserName, config.databasePassword, config.databaseName)
			
			sql = "SELECT us.id, us.name FROM users AS us WHERE us.id = %s" % id
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


def add():
	apps = list(getUserApps(id))
	apps.append({'appname':'__base__'})
	
	user = getUser(id)
	
	chainUser = Chain("USER_%s" % ip.replace('.', '_'))
	chainUser.add()
	chainUser.flush()
	chainUser.commit()
	
	for app in apps:
		if qip_rules.rules.has_key(app["appname"]):
			print qip_rules.rules[app["appname"]]
			
			rules = qip_rules.rules[app["appname"]]
			for rule in rules:
				r = chainUser.addRule(ip, rule['dest'], rule['proto'], rule['sport'], rule['dport'], "ACCEPT")
				log.log(3, "addRule: %s" % r.ruleAddString)
	
	r = chainUser.addRule(None, None, None, None, None, "LOG", '--log-prefix "DROP from %s: "' % user['name'])
	log.log(3, "addRule: %s" % r.ruleAddString)
	
	chainUser.commit()
	
	chainForward = Chain("FORWARD")
	chainForward.addRule(ip, None, None, None, None, chainUser.name)
	chainForward.commit()

def delete():
	chainUser = Chain("USER_%s" % ip.replace('.', '_'))
	chainUser.remove()
	
	chainForward = Chain("FORWARD")
	chainForward.removeRule(ip, None, None, None, None, chainUser.name)
	chainForward.commit()
	
	chainUser.commit()

if action == "add":
	delete()
	add()
elif action == "delete":
	delete()