import urllib2, smtplib

class Sms(object):
	def __init__(self, handler, options):
		self.handler = handler
		self.options = options
	
	def send(self, number, message):
		try:
			if self.handler == "mail":
				return self.sendmail(number, message)
			elif self.handler == "curl":
				return self.curl(number, message)
		except Exception, e:
			raise Exception(e, "SMS is Not Send")
				
		
	def sendmail(self, number, msg):
		smtp = smtplib.SMTP(self.options["smtphost"])
		smtp.sendmail(self.options["sender"], self.options["recipient"].replace("%number", number), self.options["msg"].replace("%msg", msg))
		smtp.close()
		
		return "OK"
		
	def curl(self, number, msg):
		 return urllib2.urlopen(self.options["url"], self.options["data"].replace("%number", number).replace("%msg", msg))