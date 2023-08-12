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

	finally:
		# Close the database
		db_conn.close()

#
# Get fields
#
def get_table(table_name, cur=None):

	# Connect to db if required
	if not cur:
		db_conn, db_cur = open_db()

	# Get table rows
	table_rows = []
	db_cur.execute(f"select * from {table_name}")
	table_rows = db_cur.fetchall()

	# Package table data
	table_data = { "name": table_name, "rows": table_rows }

	return table_data