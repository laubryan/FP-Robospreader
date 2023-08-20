#
# Processing functions
#
import base64
import cv2
import io
import matplotlib.pyplot as plt
import numpy as np
import pytesseract
import re
import torch

from gtts import gTTS
from io import BytesIO
from PIL import Image
from transformers import DetrFeatureExtractor, TableTransformerForObjectDetection

#
# Check if columns are closely adjacent
#
def are_columns_adjacent(box1, box2):
  return abs(box2[2] - box1[0]) < 2 or abs(box1[2] - box2[0]) < 2

#
# Calculate the bounding box area
#
def box_area(box):
  return (box[2]-box[0]) * (box[3]-box[1])

#
# Convert image string to image
#
def convert_image_string(page_image_string):

	# Strip base64 header
	base64_image_string = page_image_string.partition("base64,")[-1]

	# Convert base64 string to byte buffer
	image_buffer = base64.b64decode(base64_image_string)
	page_image = Image.open(io.BytesIO(image_buffer)).convert("RGB")

	return page_image

#
# Convert cell text to base64 audio string
#
def create_audio_string(cell_text):

	# Define base64 audio prefix
	base64_audio_prefix = "data:audio/mp3;base64,"

	# Remember negative numbers
	negative = False
	normalized_text = cell_text.strip()
	if normalized_text.startswith("(") and normalized_text.endswith(")"):
		negative = True

	# Prep cell text
	normalized_text = re.sub(r"[(), ]", "", cell_text) # Remove non-read chars

	# Convert text to audio
	base64_audio_string = ""
	if normalized_text:

		# Don't separate small numbers
		if len(normalized_text) > 2:

			# Space out characters
			normalized_text = " ".join(normalized_text)

			# Say special words
			normalized_text = normalized_text.replace(".", "point")	# Decimal point
			normalized_text = normalized_text.replace("0", "zero")	# Zero
			if negative:
				normalized_text = "minus " + normalized_text # Negative

		# Convert text to speech
		cell_audio = gTTS(text=normalized_text, lang="en", slow=False)

		# Convert audio to base64
		audio_buffer = BytesIO()
		cell_audio.write_to_fp(audio_buffer)
		audio_buffer.seek(0)
		base64_audio_string = base64_audio_prefix + base64.b64encode(audio_buffer.read()).decode("utf-8")

	return base64_audio_string

#
# Convert image to base64 string
#
def create_image_string(cell_image):

	# Define base64 image prefix
	base64_image_prefix = "data:image/png;base64,"

	# Convert image to base64 string
	cell_image_buffer = BytesIO()
	cell_image.save(cell_image_buffer, format="PNG")
	base64_image_string = base64_image_prefix + base64.b64encode(cell_image_buffer.getvalue()).decode("utf-8")

	return base64_image_string

#
# Global adaptive thresholding
#
# Returns: binarized array
#
def global_adaptive_thresholding(image, height, width, depth):

	# Convert image to array
	image_array = np.asarray(image)
	image_array = image_array.reshape((height, width, depth))

	# Convert image to grayscale
	grayscale_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)

	# Apply Otsu thresholding
	otsu_threshold, binarized_array = cv2.threshold(grayscale_image, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

	return binarized_array

#
# Return row bounding box from page text
#
def group_text_into_rows(page_text_pd, table_box):

	# Assemble text into rows
	rows_dict = dict()
	for index, text_data in page_text_pd.iterrows():

		# Get text top coordinate
		text_top = text_data["top"]

		# Only add elements that are within vertical table boundaries
		if text_top >= table_box[1] and text_top <= table_box[3]:

			# Check if row exists in dict
			if text_top in rows_dict:

				# Update row bounding box
				text_row = rows_dict[text_top]
				rows_dict[text_top] = {
					"left": min(text_row["left"], text_data["left"]),
					"top": min(text_row["top"], text_data["top"]),
					"right": max(text_row["right"], text_data["right"]),
					"bottom": max(text_row["bottom"], text_data["bottom"])
				}
			else:

				# Add new row
				rows_dict[text_top] = {
					"left": text_data["left"],
					"top": text_data["top"],
					"right": text_data["right"],
					"bottom": text_data["bottom"]
				}

	# Assemble row boxes
	row_boxes = [row for _, row in rows_dict.items()]

	# Page does not contain a table
	if not row_boxes:
		return row_boxes, None, None

	# Compute row height frequencies
	row_heights = {}
	for row_box in row_boxes:
		row_height = row_box["bottom"] - row_box["top"]
		row_heights[row_height] = row_heights.get(row_height, 0) + 1

	# Compute baseline row height and acceptable range
	computed_row_height = max(row_heights, key=row_heights.get)
	computed_row_heights = list(range(int(computed_row_height * 0.5), int(computed_row_height * 2)))

	# Filter rows that are too short or tall
	row_boxes = [row_box for row_box in row_boxes if (row_box["bottom"] - row_box["top"]) in computed_row_heights]

	# Merge similar row boxes
	row_boxes = merge_similar_row_boxes(row_boxes, computed_row_height)

	# Sort boxes top to bottom
	row_boxes = sorted(row_boxes, key=lambda x: x["top"])

	# Extract outer horizontal extents
	typical_rows = [row_box for row_box in row_boxes if (row_box["bottom"] - row_box["top"]) == computed_row_height]
	row_left = table_box[0]
	row_right = table_box[2]
	for row_box in typical_rows:
		if row_box["left"] < row_left:
			row_left = row_box["left"]
		if row_box["right"] > row_right:
			row_right = row_box["right"]
	row_left -= 1
	row_right += 5

	# Convert to tuples and filter out rows that aren't wide enough
	min_width_ratio = 0.6
	table_width = row_right - row_left
	row_boxes = [(row_box["left"], row_box["top"], row_box["right"], row_box["bottom"]) for row_box in row_boxes if ((row_box["right"] - row_box["left"]) / table_width) > min_width_ratio ]

	# Normalize rows to horizontal extents
	row_boxes = [(row_left, row_box[1], row_box[2], row_box[3]) for row_box in row_boxes]

	return row_boxes, row_left, row_right

#
# Identify page text
#
def identify_page_text(image):

	# OCR page text
	page_pd_ocr = pytesseract.image_to_data(image, output_type="data.frame")

	# Drop any rows that identify blank text
	page_pd_ocr.dropna(subset=["text"], inplace=True)

	# Calculate other position values
	page_pd_ocr["right"] = page_pd_ocr["left"] + page_pd_ocr["width"]
	page_pd_ocr["bottom"] = page_pd_ocr["top"] + page_pd_ocr["height"]

	# Reset the dataframe index
	page_pd_ocr.reset_index(inplace=True)

	return page_pd_ocr

#
# Identify table columns
#
# - Returns column list, first column is leftmost item label column
#
def identify_table_columns(binarized_image, table_location, page_text_df, num_rows):

	# Instantiate model
	table_model_structure = TableTransformerForObjectDetection.from_pretrained("microsoft/table-transformer-structure-recognition")

	# Instantiate DETR model feature extractor
	# https://arxiv.org/abs/2005.12872
	image = binarized_image
	feature_extractor = DetrFeatureExtractor()
	encoding = feature_extractor(image, return_tensors="pt")

	# Infer table location and structure
	with torch.no_grad():
		ts_outputs = table_model_structure(**encoding)

	target_sizes = [image.size[::-1]]
	ts_results = feature_extractor.post_process_object_detection(ts_outputs, threshold=0.7, target_sizes=target_sizes)[0]

	# Extract only columns
	max_column_area = (table_location[2] - table_location[0]) * (table_location[3] - table_location[1]) * 0.8
	column_boxes = [box for box in ts_results['boxes'] if is_column(box) and box_area(box)<max_column_area]

	# Sort columns left to right
	column_boxes = sorted(column_boxes, key=lambda box: box[0])

	# Merge overlapping columns
	overlap_threshold = 0.2
	output_columns = []
	for column_box in column_boxes:

		# Add initial box
		if not output_columns:
			output_columns.append(column_box)
			continue
		else:

			# Compute column area
			column_area = (column_box[2] - column_box[0]) * (column_box[3] - column_box[1])

			# Compare candidate column with each preserved column
			column_was_merged = False
			for output_box in output_columns:

				# Calculate intersection over union (IoU)
				output_area = (output_box[2] - output_box[0]) * (output_box[3] - output_box[1])
				intersection_area = (min(column_box[2], output_box[2]) - max(column_box[0], output_box[0])) * (output_box[3] - output_box[1])
				union_area = column_area + output_area
				iou = intersection_area / union_area

				# Merge overlapping columns based on IoU threshold
				if iou > overlap_threshold:
					merged_column = [min(output_box[0], column_box[0]), output_box[1], max(output_box[2], column_box[2]), output_box[3]]
					output_columns.append(merged_column)
					column_was_merged = True
					break
				
			# Add column if not close
			if not column_was_merged:
				output_columns.append(column_box)
	column_boxes = output_columns

	# Page does not contain a column, 
	# therefore most likely not a table
	if not column_boxes:
		return []

	# Discard rightmost columns that don't contain enough numbers
	column_digits_threshold = 0.8 # The ratio of cells that must contain numbers
	valid_column_boxes = [column_boxes[0]]
	for i, col_box in enumerate(column_boxes[1:]):

		# Get text for any cells within the column boundaries
		col_text_series = page_text_df[
			(page_text_df["left"] >= int(col_box[0])) & 
			(page_text_df["right"] <= int(col_box[2])) & 
			(page_text_df["top"] >= int(table_location[1])) & 
			(page_text_df["bottom"] <= int(table_location[3]))
			]["text"]

		# Count the number of digits
		digits_count = col_text_series.str.contains("[0-9]").value_counts()

		# Reject columns that don't contain enough digits
		if True in digits_count:

			# Calculate percentage of cells with digits for this column
			number_cells_ratio = digits_count.loc[True] / num_rows

			# Only keep columns that meet the threshold amount
			if number_cells_ratio >= column_digits_threshold:
				valid_column_boxes.append(col_box)
	column_boxes = valid_column_boxes

	# Clip columns to table boundaries
	column_boxes = [(max(column_box[0], table_location[0]), table_location[1], min(column_box[2], table_location[2]), table_location[3]) for column_box in column_boxes]

	# Extend first column to left edge
	column_boxes[0] = (min(column_boxes[0][0], table_location[0]), column_boxes[0][1], column_boxes[0][2], column_boxes[0][3])

	return column_boxes

#
# Check if bounding box is a column
#
def is_column(box):
  if (box[2]-box[0]) < (box[3]-box[1]):
    return True
  return False

#
# Merge similar rows
#
def merge_similar_row_boxes(row_boxes, row_height):

	output_boxes = []

	# Process all row boxes
	proximity_tolerance = int(row_height * 0.5)
	for row_box in row_boxes:

		# Add initial box
		if not output_boxes:
			output_boxes.append(row_box)
			continue

		else:

			# Get current row middle
			current_middle = row_box["top"] + (row_box["bottom"] - row_box["top"])

			# Check for approximate top value key
			matched_row = False
			for output_idx, output_row in enumerate(output_boxes):
				
				# Calculate output box middle
				output_middle = output_row["top"] + (output_row["bottom"] - output_row["top"])

				# Merge bounding boxes if middles are close
				middle_distance = abs(output_middle - current_middle)
				if middle_distance <= proximity_tolerance:
					matched_row = True
					break

			# Merge close matches
			if matched_row:
				output_boxes[output_idx] = {
					"left": min(output_row["left"], row_box["left"]),
					"top": min(output_row["top"], row_box["top"]),
					"right": max(output_row["right"], row_box["right"]),
					"bottom": max(output_row["bottom"], row_box["bottom"]),
				}
			else:
				# No approximate match, so add row to output as a new unique row
				output_boxes.append(row_box)

	return output_boxes

#
# Parse row data
#
def parse_rows(page_image, row_boxes, column_boxes, page_text_df):

	# Define boxes
	label_column_box = column_boxes[0]
	data_column_box = column_boxes[1]
	
	# Process each row
	row_elements = []
	for row_box in row_boxes:

		# Define cell boxes
		label_cell_box = (int(label_column_box[0]), int(row_box[1]), int(label_column_box[2]), int(row_box[3]))
		data_cell_box = (int(data_column_box[0]), int(row_box[1]) - 1, int(data_column_box[2]), int(row_box[3]) + 1)

		# Extract label text
		label_text_series = page_text_df[
			(page_text_df["left"] >= label_cell_box[0]) & 
			(page_text_df["right"] <= label_cell_box[2]) & 
			(page_text_df["top"] >= label_cell_box[1]) & 
			(page_text_df["bottom"] <= label_cell_box[3])
			]
		label_text = " ".join(label_text_series["text"]).strip()

		# Extract data text
		data_text_series = page_text_df[
			(page_text_df["left"] >= data_cell_box[0]) & 
			(page_text_df["right"] <= data_cell_box[2]) & 
			(page_text_df["top"] >= data_cell_box[1]) & 
			(page_text_df["bottom"] <= data_cell_box[3])
			]
		data_text = " ".join(data_text_series["text"]).strip()

		# Strip non-value characters from all elements
		data_text = re.sub(r"[^0-9(). ]+", "", data_text)

		# Strip mismatched parentheses
		if "(" in data_text and ")" not in data_text:
			data_text = data_text.replace("(", "")
		elif "(" not in data_text and ")" in data_text:
			data_text = data_text.replace(")", "")

		# Extract data cell image
		data_image = page_image.crop((data_cell_box[2] - 180, data_cell_box[1], data_cell_box[2], data_cell_box[3]))

		# Assemble row
		row_element = { "label": label_text, "value": data_text, "cell_image": data_image }
		row_elements.append(row_element)

	# Assemble rows bundle
	num_rows = len(row_elements)
	rows_bundle = { "elements": row_elements, "num_extracted_values": num_rows }

	return rows_bundle

#
# Extract data from image
#
def process_image(page_image):

  # Parse image dimensions
	page_width = page_image.width
	page_height = page_image.height
	page_depth = 3
	print(f"Image dimensions: {page_width} x {page_height} x {page_depth}")

	# Binarize image
	binarized_array = global_adaptive_thresholding(page_image, page_height, page_width, page_depth)

	# Display image
	binarized_image = Image.fromarray(binarized_array).convert("RGB")

	# Segment table
	table_location = segment_table(binarized_image)
	if table_location == None:
		return None
	
	# Identify entire page text
	page_text_df = identify_page_text(page_image)

	# Group page text into rows
	row_boxes, row_left, row_right = group_text_into_rows(page_text_df, table_location)

	# If there are no detected rows, then likely not a table
	if not row_boxes:
		return []

	# Adjust horizontal table boundaries based on detected row data
	if row_left < table_location[0]:
		table_location[0] = row_left
	if row_right > table_location[2]:
		table_location[2] = row_right

	# Identify table columns
	column_boxes = identify_table_columns(binarized_image, table_location, page_text_df, len(row_boxes))

	# If there are no detected columns, then likely not a table
	if not (column_boxes and len(column_boxes) > 0):
		return []

	# Parse the rows
	row_data = parse_rows(page_image, row_boxes, column_boxes, page_text_df)

	# Assemble validation data
	validation_data = []
	for element in row_data["elements"]:

		# Convert cell to base64 image
		cell_image_string = create_image_string(element["cell_image"])

		# Convert cell to base64 audio
		cell_audio_string = create_audio_string(element["value"])

		# Assemble data element
		validation_data.append({"label": element["label"], "extracted_value": element["value"], "cell_image": cell_image_string, "audio": cell_audio_string })

	# Return validation data
	return validation_data

#
# Segment table
#
def segment_table(binarized_image):

	# Instantiate model
	table_model_location = TableTransformerForObjectDetection.from_pretrained("microsoft/table-transformer-detection")

	# Instantiate DETR model feature extractor
	# https://arxiv.org/abs/2005.12872
	image = binarized_image
	feature_extractor = DetrFeatureExtractor()
	encoding = feature_extractor(image, return_tensors="pt")

	# Infer table location and structure
	with torch.no_grad():
		tl_outputs = table_model_location(**encoding)

	width, height = image.size
	location_results = feature_extractor.post_process_object_detection(tl_outputs, threshold=0.2, target_sizes=[(height, width)])[0]

	# No table detected
	num_table_boxes = len(location_results['boxes'])
	if num_table_boxes == 0:
		return None

	# Extract table location
	padding = 5
	table_location = location_results["boxes"][0].tolist()
	table_location = [table_location[0] - padding, table_location[1], table_location[2] + padding, table_location[3]]

	return table_location