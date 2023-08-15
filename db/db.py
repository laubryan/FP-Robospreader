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
# Get list of actual test values
#
def get_actual_values(test_number):

	# Get value rows
	value_rows = get_test_data(test_number)

	# Extract values
	actual_values = []
	for row in value_rows:
		actual_values.append(row["actual_value"])

	return actual_values

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

#
# Get test data
#
def get_test_data(test_number):

	# Get test data
	if test_number == 1:
		return get_test1()
	else:
		return get_test2()
	
#
# Save test results
#
def save_test_results(test_id, test_number, elapsed_time_ms, num_errors):

	# Connect to db if required
	db_conn, db_cur = open_db()

	# Insert Test 1 data
	if test_number == 1:

		# Insert data
		queryParams = [elapsed_time_ms, num_errors]
		db_cur.execute("insert into results (test1_time, test1_errors) values (?, ?)", queryParams)

	else:

		# Update Test 2 data
		queryParams = [elapsed_time_ms, num_errors, test_id]
		db_cur.execute("update results set test2_time = ?, test2_errors = ? where id = ?", queryParams)

	# Get affected row ID
	row_id = db_cur.lastrowid

	# Commit
	db_conn.commit()

	return row_id