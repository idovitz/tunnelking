##################################################
# projectname: tunnelking
# Copyright (C) 2009  IJSSELLAND ZIEKENHUIS
##################################################

import MySQLdb
import sys

class DBmysql:
	def __init__(self, user, passwd, db):
		#connect to db
		self.db = MySQLdb.connect(db=db, user=user, passwd=passwd)
		try:	
			self.cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
		except MySQLdb.Error, msg:
			print msg
			sys.exit()
		
	# execute query
	def execSQL(self,sql):
		try:
			self.cursor.execute(sql)
		except MySQLdb.Error, msg:
			print msg
			print sql
		
	# execute query + get results
	def querySQL(self,sql):
		try:
			self.cursor.execute(sql)
		except MySQLdb.Error, msg:
			print msg
			print sql
			sys.exit()
		try:
			results = self.cursor.fetchall()
		except MySQLdb.Error, msg:
			print msg
			sys.exit()
		return results
	
	def newCursor(self):
		self.db.commit()
		self.cursor.close()
		try:	
			self.cursor = self.db.cursor()
		except MySQLdb.Error, msg:
			print msg
			sys.exit()
		
	# get field names
	def getFieldNames(self,tablename):
		try:	
			cursor = self.db.cursor()
		except MySQLdb.Error, msg:
			print msg
			sys.exit()
		
		try:
			cursor.execute("""SELECT * FROM """+tablename+""" LIMIT 1""")
		except MySQLdb.Error, msg:
			print msg
			sys.exit()
		
		desc = cursor.description
		cursor.close()
		
		fieldnames = []
		for f in desc:
			fieldnames.append(f[0])
		return fieldnames
	
	def __del__(self):
		self.db.close()
		
