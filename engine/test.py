#
# Validation Test Functions
#
from db import db
from engine import processor

#
# Get value rows for both tests
#
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


#
# Save test results
#
def save_test_results(test_id, test_number, elapsed_time_ms, input_values):

	# Get actual test values
	actual_values = db.get_actual_values(test_number)

	# Compare actual and input values
	correct_values = [actual_value for actual_value, input_value in zip(actual_values, input_values) if actual_value == input_value]
	num_errors = len(actual_values) - len(correct_values)

	# Save values to db
	test_id = db.save_test_results(test_id, test_number, elapsed_time_ms, num_errors)

	return test_id
