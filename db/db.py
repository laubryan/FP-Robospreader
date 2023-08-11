#
# Database Functions
#
import sqlite3

#
# Open db and get cursor
#
def open_db():

	# Connect/create database
	db_conn = sqlite3.connect("db/test.db")
	db_cur = db_conn.cursor()

	return db_conn, db_cur

#
# Initialize Database
#
def initialize():
  
	try:

		# Read setup script
		with open("db/setup.sql", "r") as setup_script:
			setup_sql = setup_script.read()

		# Open db
		db_conn, db_cur = open_db()

		# Create fields table
		db_cur.executescript(setup_sql)

		# Status
		data = fields(db_cur)
	
	finally:
		# Close the database
		db_conn.close()

	return data

#
# Get fields
#
def fields(cur):

	# Get fields
	fields = []
	cur.execute("select * from fields")
	fields = cur.fetchall()

	return fields