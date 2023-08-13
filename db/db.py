#
# Database Functions
#
import sqlite3

#
# Custom row factory
#
# - From: https://docs.python.org/3/library/sqlite3.html#sqlite3-howto-row-factory
#
def dict_factory(cursor, row):
	fields = [column[0] for column in cursor.description]
	return {key: value for key, value in zip(fields, row)}

#
# Open db and get cursor
#
def open_db():

	# Connect/create database
	db_conn = sqlite3.connect("db/test.db")

	# Configure row dictionaries
	#db_conn.row_factory = sqlite3.Row
	db_conn.row_factory = dict_factory

	# Get db cursor
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

#
# Get Test 1 data
#
def get_test1():

	# Connect to db if required
	db_conn, db_cur = open_db()

	# Get table rows
	table_rows = []
	db_cur.execute(f"select f.name, f.actual_value from tests t, fields f where t.test_id = 1 and t.field_id = f.id")
	table_rows = db_cur.fetchall()

	return table_rows

#
# Get Test 2 data
#
def get_test2():

	# Connect to db if required
	db_conn, db_cur = open_db()

	# Get table rows
	table_rows = []
	db_cur.execute(f"select f.id, f.name, f.actual_value, f.extracted_value from tests t, fields f where t.test_id = 2 and t.field_id = f.id")
	table_rows = db_cur.fetchall()

	return table_rows