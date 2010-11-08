import os, config

class Chain:
	def __init__(self, name):
		self.name = name
		self.actions = []
		self.rules = []
	
	def add(self):
		self.actions.append("-N %s" % self.name)
	
	def remove(self):
		self.actions.append("-F %s" % self.name)
		self.actions.append("-X %s" % self.name)
		
	def addRule(self, source, dest, proto, sport, dport, target, extra=""):
		rule = Rule(self.name, source, dest, proto, sport, dport, target, extra)
		
		self.rules.append(rule)
		self.actions.append(rule.ruleAddString)
		
		return rule
	
	def removeRule(self, source, dest, proto, sport, dport, target, extra=""):
		rule = Rule(self.name, source, dest, proto, sport, dport, target, extra)
		
		self.rules.append(rule)
		self.actions.append(rule.ruleRemoveString)
		
		return rule
	
	def setPolicy(self, policy):
		self.actions.append("-P %s %s" % (self.name, policy))
	
	def flush(self):
		self.actions.append("-F %s" % self.name)
	
	def commit(self):
		for action in self.actions:
			os.system("%s %s" % (config.iptPath, action))
		
		self.actions = []

class Rule:
	def __init__(self, chain, source, dest, proto, sport, dport, target, extra):
		self.ruleAddString = "-A %s" % chain
		self.ruleRemoveString = "-D %s" % chain
		ruleString = ""
		
		if source != None:
			ruleString += " -s %s" % source
			
		if dest != None:
			ruleString += " -d %s" % dest
		
		if proto != None:
			ruleString += " -p %s" % proto
		
		if sport != None:
			ruleString += " --sport %s" % sport
		
		if dport != None:
			ruleString += " --dport %s" % dport
		
		ruleString += " -j %s" % target
			
		ruleString += " %s" % extra
		
		self.ruleAddString += ruleString
		self.ruleRemoveString += ruleString