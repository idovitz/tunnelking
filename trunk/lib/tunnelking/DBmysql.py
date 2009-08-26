##################################################
# projectname: tunnelking
# Copyright (C) 2009  IJSSELLAND ZIEKENHUIS
##################################################

import MySQLdb
import sys

class DBmysql:
	def __init__(self, user, passwd, dbname):
		self.user, self.passwd, self.dbname = user, passwd, dbname
		self.connect()
	
	def connect(self):
		#connect to db
		self.db = MySQLdb.connect(db=self.dbname, user=self.user, passwd=self.passwd)
		try:	
			self.cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
		except MySQLdb.Error, e:
			raise Exception(e, "")
	
	def checkConnection(self):
		try:
			self.db.ping()
		except:
			self.connect()
			
	# execute query
	def execSQL(self,sql):
		self.checkConnection()
		
		try:
			self.cursor.execute(sql)
		except MySQLdb.Error, e:
			raise Exception(e, sql)
		
	# execute query + get results
	def querySQL(self,sql):
		self.checkConnection()
		
		try:
			self.cursor.execute(sql)
		except MySQLdb.Error, e:
			raise Exception(e, sql)

		try:
			results = self.cursor.fetchall()
			return results
		except MySQLdb.Error, e:
			raise Exception(e, sql)
	
	def newCursor(self):
		self.db.commit()
		self.cursor.close()
		try:	
			self.cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
		except MySQLdb.Error, e:
			raise Exception(e, "")
		
	# get field names
	def getFieldNames(self,tablename):
		self.checkConnection()
		
		try:	
			cursor = self.db.cursor()
		except MySQLdb.Error, e:
			raise Exception(e, "")
		
		try:
			cursor.execute("""SELECT * FROM """+tablename+""" LIMIT 1""")
		except MySQLdb.Error, e:
			raise Exception(e, "")
		
		desc = cursor.description
		cursor.close()
		
		fieldnames = []
		for f in desc:
			fieldnames.append(f[0])
		return fieldnames
	
	def close(self):
		try:
			self.db.close()
		except:
			self.db = None
				
	def __del__(self):
		self.close()
		
