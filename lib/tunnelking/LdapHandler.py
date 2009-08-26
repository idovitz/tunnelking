import sys, ldap


class LdapHandler:
	def __init__(self, ip, dn, sf, bd, bp):
		print ip, dn, sf, bd, bp
		self.ip = ip
		self.bd = bd
		self.bp = bp
		self.dn = dn
		self.sf = sf
		
		self.connect()
	
	def connect(self):
		try:
			self.con = ldap.open(self.ip)
			self.con.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
			self.con.set_option(ldap.OPT_REFERRALS, 0)
			self.con.start_tls_s()
			self.con.simple_bind_s(self.bd, self.bp)
		except Exception, e:
			print e
	
	def search(self, str):
		try:
			result = self.con.search_s(self.dn, ldap.SCOPE_SUBTREE, "(&%s (objectClass=person))" % (self.sf.replace("%u", "*%s*") % str), ['samAccountName'])
		except Exception, e:
			result = [type(e), e]
			try:
				self.connect()
			except Exception, e:
				result = [type(e), e]
			
		return result