#
# Validation Test Functions
#
from db import db
from engine import processor

def get_test_data():
    
	# Get test data from database
	test1_rows = db.get_test1()
	test2_rows = db.get_test2()

	# Convert Test 2 values to base64 audio
	test2_data = []
	for row in test2_rows:

		# Convert value to audio string
		cell_value = str(row["extracted_value"])
		cell_audio_string = processor.create_audio_string(cell_value)

		# Add to row
		row["audio"] = cell_audio_string

	return test1_rows, test2_rows