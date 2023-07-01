#
# Processing functions
#
import base64
import cv2
import io
import numpy as np
import pytesseract
import re
import torch

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
# Check if bounding boxes overlap
#
def boxes_overlap(box1, box2, overlap_ratio=0.4):
  dx = min(box1[2], box2[2]) - max(box1[0], box2[0])
  dy = min(box1[3], box2[3]) - max(box1[1], box2[1])
  area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
  area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
  if (dx >= 0) and (dy >= 0):
    overlap_area = dx * dy
    overlap_ratio1 = overlap_area / area1
    overlap_ratio2 = overlap_area / area2
    if overlap_ratio1 > overlap_ratio or overlap_ratio2 > overlap_ratio:
      return True
  return False

#
# Extract data from image
#
def processImage(page_image_string):

	# Strip base64 header
	base64_image_string = page_image_string.partition("base64,")[-1]

	# Convert base64 string to byte buffer
	image_buffer = base64.b64decode(base64_image_string)
	page_image = Image.open(io.BytesIO(image_buffer)).convert("RGB")

  # Parse image dimensions
	page_width = page_image.width
	page_height = page_image.height
	page_depth = 3
	# print(f"Image dimensions: {page_width} x {page_height} x {page_depth}")

	# Binarize image
	binarized_array = global_adaptive_thresholding(page_image, page_height, page_width, page_depth)

	# Display image
	binarized_image = Image.fromarray(binarized_array).convert("RGB")

	# Segment table
	table_location = segmentTable(binarized_image)
	# print(f"Table location: {table_location}")

	# Identify table structure
	column_boxes = identifyTableStructure(binarized_image, table_location)

	# Identify entire page text
	page_text = identifyPageText(page_image)

	# Extract first column text
	first_column_text = extractFirstColumnText(page_text, table_location, column_boxes)

	# Identify line item labels
	line_item_labels = identifyLineItemLabels(first_column_text)
	print(line_item_labels)

	# Extract complete data elements
	data_elements = extractLineItemElements(line_item_labels, page_text, column_boxes, page_image)
	# print(data_elements)

	# DEBUG: Write image to test file
	page_image.save("test-color.png")
	binarized_image.save("test-binarized.png")

	# DEBUG: Dummy validation data
	# validation_data = [
	# 		{ "label": "Short-term investments", "extracted_value": "3799", "original_value": "3799" },
	# 		{ "label": "Accounts receivable", "extracted_value": "926", "original_value": "926" },
	# 		{ "label": "Total current assets", "extracted_value": "7516", "original_value": "7516" },
	# 		{ "label": "Investments deposits and other assets", "extracted_value": "936", "original_value": "936" },
	# 		{ "label": "Deferred income tax", "extracted_value": "134", "original_value": "134" },
	# 		{ "label": "Total current liabilities", "extracted_value": "7775", "original_value": "7775" },
	# 		{ "label": "Total shareholders equity", "extracted_value": "4400", "original_value": "4400" },
	# ]

	# Assemble validation data
	validation_data = []
	base64_image_prefix = "data:image/png;base64,"
	for element in data_elements["elements"]:

		# Convert cell image to base64
		cell_image_buffer = BytesIO()
		element["cell_image"].save(cell_image_buffer, format="PNG")
		# base64_image_text = base64_image_prefix + base64.b64encode(cell_image_buffer.getvalue())
		base64_image_string = base64_image_prefix + base64.b64encode(cell_image_buffer.getvalue()).decode("utf-8")

		# Assemble data element
		validation_data.append({"label": element["label"], "extracted_value": element["value"], "cell_image": base64_image_string })

	# Return validation data
	return validation_data

#
# Extract text contained in leftmost column
#
def extractFirstColumnText(text_data, table_location, column_boxes):

		# Filter first column (fc) elements
	fc_box = column_boxes[0]
	fc_pd = text_data[(text_data["right"]) < int(fc_box[2])] # Constrain to first column
	fc_pd = text_data[(text_data["top"]) >= int(table_location[1])] # Constrain to table
	fc_pd = fc_pd.dropna(subset=["text"]) # Drop NaN rows
	fc_pd = fc_pd[fc_pd["text"].str.isspace() & fc_pd["text"] != ""] # Drop rows that have blank text
	fc_pd.reset_index(inplace=True)
	# print(f"Column number of fields: {len(fc_pd)}")

	return fc_pd

#
# Extract line item elements
#
def extractLineItemElements(line_item_labels, text_data, column_boxes, page_image):

	# Count line item labels
	num_line_item_labels = len(line_item_labels)

	# Get column bounding box
	prospective_elements = []
	for fc_box in column_boxes:

		# Extract elements
		elements, num_extracted_values = extract_column_elements(fc_box, line_item_labels, text_data, page_image)
		prospective_elements.append({ "elements": elements, "num_extracted_values": num_extracted_values })

	# Prefer the leftmost column with at least half of the values
	best_values = None
	acceptable_threshold = int(num_line_item_labels * 0.5)
	for elements in prospective_elements:
		if elements["num_extracted_values"] > acceptable_threshold:
			best_values = elements
			break

	# Otherwise just use the best column
	if best_values == None:
		best_values = sorted(prospective_elements, key=lambda x: x["num_extracted_values"], reverse=True)[0]

	# Display the results
	# print(f"Extracted values: {best_values['num_extracted_values']} of {num_line_item_labels}")

	return best_values

#
# Extract line elements for the designated column
#
def extract_column_elements(column_box, df_labels, df_page_ocr, page_image):

	# Extract first column cells for each line item
	elements = []
	v_tolerance = 12
	num_extracted_values = 0
	for row in df_labels.itertuples():

		# Extract OCR text for cell in this column
		val_pd = df_page_ocr[\
			(df_page_ocr["left"] >= int(column_box[0])) & ((df_page_ocr["right"]) <= int(column_box[2])) & \
			(df_page_ocr["top"] >= int(row.top - v_tolerance)) & ((df_page_ocr["bottom"]) <= int(row.bottom + v_tolerance))
		]

		# Extract cell image
		cell_image = page_image.crop((int(column_box[0]), row.top, int(column_box[2]), row.bottom))

		# Only save value if it's not blank
		if not val_pd.empty:

			# Get the list of values (there can be more than one)
			cell_values = val_pd["text"].values

			# Strip non-value characters from all elements
			cell_values = [re.sub(r"[^0-9(). ]+", "", element) for element in cell_values]

			# Take the first value
			cell_value = cell_values[0]
			if cell_value.strip() != "":

				# Count extracted value
				num_extracted_values += 1

		else:
			cell_value = ""

		# Save element data
		element = { "label": row.text, "value": cell_value, "cell_image": cell_image }
		elements.append(element)

	return elements, num_extracted_values

# Global adaptive thresholding
# Returns: binarized array
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
# Identify line item labels
#
def identifyLineItemLabels(text_data):

	# Concatenate words and widths
	line_item_labels_pd = text_data
	line_item_labels_pd = text_data\
		.groupby(["par_num", "line_num"])\
		.agg({"text": " ".join, "left": "first", "top": "first", "width": "sum", "height": "max"})\
		.reset_index()

	# Calculate other fields
	line_item_labels_pd["bottom"] = line_item_labels_pd["top"] + line_item_labels_pd["height"]

	# Format label
	inter_word_gap = 5
	line_item_labels_pd["text"].replace(r"[^0-9a-zA-Z ]+", "", regex=True, inplace=True) # Strip non-alphanumeric chars
	line_item_labels_pd["text"].replace(r"[\d ]+$", "", regex=True, inplace=True) # Strip trailing numbers

	# Drop non-essential columns
	line_item_labels_pd.drop(columns=["par_num", "line_num"], inplace=True)

	# Drop labels that are too long to be realistic
	line_item_labels_pd = line_item_labels_pd[line_item_labels_pd["width"] < 250]
	line_item_labels_pd.reset_index(inplace=True)

	# Compute peak left margins
	# histogram, bin_margins = np.histogram(fc_formatted_pd["left"], bins=10)
	# top_peak_indices = np.argsort(histogram)[-2:]
	# peak_margins = (bin_margins[:-1] + bin_margins[1:]) / 2
	# print(np.round(peak_margins[top_peak_indices]))

	# Count number of labels
	num_item_labels = len(line_item_labels_pd)

	return line_item_labels_pd

#
# Identify page text
#
def identifyPageText(image):

	# OCR page text
	page_pd_ocr = pytesseract.image_to_data(image, output_type="data.frame")
	page_pd_ocr.dropna(subset=["text"], inplace=True)
	# print(f"Page number of fields: {len(page_pd_ocr)}")

	# Calculate other position values
	page_pd_ocr["right"] = page_pd_ocr["left"] + page_pd_ocr["width"]
	page_pd_ocr["bottom"] = page_pd_ocr["top"] + page_pd_ocr["height"]
	page_pd_ocr.reset_index(inplace=True)

	return page_pd_ocr

#
# Identify table structure
#
def identifyTableStructure(binarized_image, table_location):

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
	# print(f"Max column area: {max_column_area}")
	column_boxes = [box for box in ts_results['boxes'] if is_column(box) and box_area(box)<max_column_area]
	num_boxes = len(column_boxes)

	# Merge closely adjacent or overlapping columns
	merged_columns = []
	removed_columns = []
	for i, box1 in enumerate(column_boxes):
		for j, box2 in enumerate(column_boxes):
			if i != j:
				# Check if columns adjacent or overlapping
				if are_columns_adjacent(box1, box2) or boxes_overlap(box1, box2):

					# Merge columns
					merged_box = torch.tensor([min(box1[0], box2[0]), min(box1[1], box2[1]), max(box1[2], box2[2]), max(box1[3], box2[3])])
					if not is_box_in_list(merged_box, merged_columns):
						merged_columns.append(merged_box)

					# Mark pieces of merged column for removal
					if not is_box_in_list(box1, removed_columns):
						removed_columns.append(box1)
					if not is_box_in_list(box2, removed_columns):
						removed_columns.append(box2)
				else:
					# Add if not already in merged list
					if not is_box_in_list(box1, merged_columns):
						merged_columns.append(box1)

	# Remove discarded columns that were merged
	column_boxes = [box for box in merged_columns if not is_box_in_list(box, removed_columns)]
	num_boxes = len(column_boxes)
	print(f"Number of columns: {num_boxes}")

	# Sort columns left to right
	column_boxes = sorted(column_boxes, key=lambda box: box[0])

	return column_boxes

#
# Check if bounding box is in the list
#
def is_box_in_list(box, list):
  return any([all(box==element) for element in [boxel for boxel in list]])

#
# Check if bounding box is a column
#
def is_column(box):
  if (box[2]-box[0]) < (box[3]-box[1]):
    return True
  return False

#
# Segment table
#
def segmentTable(binarized_image):

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

	# Extract table location
	padding = 5
	table_location = location_results["boxes"][0].tolist()
	table_location = [table_location[0] - padding, table_location[1], table_location[2] + padding, table_location[3]]

	return table_location