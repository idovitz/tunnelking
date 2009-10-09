import sys, random, string, os, time
from DBmysql import DBmysql
from Sms import Sms

class OtpKey(object):
	def __init__(self, config, log):
		self.log = log
		self.config = config
	
	def genPronounceablePassword(self, length):
		vowels='aeiou'
		consonants='bcdfghjklmnpqrstvwxyz'
		consonantsUpper = consonants.upper()
		special = "$#!@"
		digits = string.digits
		sorts = ['word', "digits", "special"]
		sorts = ['word', "digits"]
		password=''
		
		sort = random.choice(sorts)
		sortc = 0
		for i in range(length):
			newsort = False

			if sort == 'word':
				if sortc == 0 or sortc == 2: 
					password += random.choice(consonants)
					if sortc == 2:
						newsort = True
				else:
					password += random.choice(vowels)
			elif sort == 'digits':
				password += random.choice(digits)
				newsort = True
			elif sort == 'special':
				password += random.choice(special)
				newsort = True
			elif sort == 'upper':
				password += random.choice(consonantsUpper)
				newsort = True
			
			sortc += 1
			
			if newsort:
				sortc = 0
				if sorts.index(sort) != 0 or len(sorts) == 1:
					sort = 'word'
				else:
					sort = random.choice(sorts[1:3])
					
		return password
	
	def sendKey(self, user, ip, tr_ip):
		self.log.log(3, "%s %s %s" % (user, ip, tr_ip))
		key = self.genPronounceablePassword(10)
		
		if user["otpRecipient"] != "":
			try:
				# send key
				msg = "%s geldig vanaf %s geldig tot %s" % (key, ip, time.strftime("%d-%m-%Y %H:%M", time.localtime(time.time()+(60*60*12))))
				sms = Sms(self.config.smsHandler, self.config.smsOptions)
				res = sms.send(user["otpRecipient"], msg)
			
				# delete old keys for ip / user
				db = DBmysql(self.config.databaseUserName, self.config.databasePassword, self.config.databaseName)
				db.execSQL("DELETE FROM `keys` WHERE lip = '%s'" % (ip))
				
				# insert session key
				sql = "INSERT INTO `keys` (`userid`, `key`, `expiretime`, `lip`, `rip`) VALUES(%s, '%s', DATE_ADD(NOW(), INTERVAL 12 HOUR), '%s', '%s')" % (user["id"], key, ip, tr_ip)
				self.log.log(3, "sql: %s" % (sql))
				db.execSQL(sql)
				self.log.log(2, "%s sended: %s" % (key, res))
				return True
			except Exception, e:
				self.log.log(2, "OtpKey sendKey() %s: %s" % (type(e), e))
				sys.exit(1)
		else:
			self.log.log(2, "NO OTP for %s" % user["name"])
			return False