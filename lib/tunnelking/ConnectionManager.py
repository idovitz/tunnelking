import socket, telnetlib

class ConnectionManager:
	def __init__(self, host, port):
		self.host = host
		self.port = port
	
	def connect(self):
		try:
			self.tn = telnetlib.Telnet(self.host, self.port)
		except Exception, e:
			print e

	def close(self):
		self.tn.close()

	def getConnections(self):
		self.tn.write("status\n")
		m = self.tn.read_until("END", 6)
		status = {}
		
		for k, l in enumerate(m.split("\n")):
			if k >= 4 and l[0:7] != "ROUTING" and l[0:7] != "Virtual":
				if l[0:6] == "GLOBAL":
					break
				
				l = l.rstrip()
				la = l.split(",")
				
				if status.has_key(la[1]+"_"+la[2]) == True:
					status[la[1]+"_"+la[2]].append(la)
				else:
					status[la[0]+"_"+la[1]] = [la]
		self.close()
		return status

	def kill(self, target):
		ta = target.split("_")
		
		if ta[0] == "UNDEF":
			target = ta[1]
		else:
			target = ta[0]
		
		self.connect()
		self.tn.write("kill %s\n" % target)
		self.close()
	
	def __del__(self):
		self.close

#class Ask():
#	def __init__(self):
#		self.m = Manager("172.16.0.50", 7505)
#	
#	def getConnections(self, params):
#		cons = {"items":[]}
#		st = self.m.getStatus()
#		for s in st.iteritems():
#			cons["items"].append({"username":s[1][0][0], "ip_from":s[1][0][1], "ip_vpn":s[1][1][0], "bytes_send":int(s[1][0][2])/1024, "bytes_received":int(s[1][0][3])/1024, "dt_c":s[1][0][4], "dt_la":s[1][1][3]})
#		
#		return cons
#	
#	def kill(self, params):
#		self.m.kill(str(params["k"]).strip())
#		return "OK"
#	
#	def getMainTree(self,params):
#		return {"label": 'name', "identifier": 'name', "items": [{"name": 'connections', "type": 'category'}, { "name": 'configuration', "type": 'category'}, {"name":'status', "type": 'category'}]}
