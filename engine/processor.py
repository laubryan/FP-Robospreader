#
# Processing functions
#
import base64
import cv2
import io
import numpy as np
import torch

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
# Convert image to data
#
def convertImage(page_image_string):

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
	print(f"Table location: {table_location}")

	# Identify table structure
	column_boxes = identifyTableStructure(binarized_image, table_location)

	# DEBUG: Write image to test file
	page_image.save("test.png")
	binarized_image.save("test-binarized.png")

	# DEBUG
	validation_data = [
			{ "label": "Short-term investments", "extracted_value": "3799", "original_value": "3799" },
			{ "label": "Accounts receivable", "extracted_value": "926", "original_value": "926" },
			{ "label": "Total current assets", "extracted_value": "7516", "original_value": "7516" },
			{ "label": "Investments deposits and other assets", "extracted_value": "936", "original_value": "936" },
			{ "label": "Deferred income tax", "extracted_value": "134", "original_value": "134" },
			{ "label": "Total current liabilities", "extracted_value": "7775", "original_value": "7775" },
			{ "label": "Total shareholders equity", "extracted_value": "4400", "original_value": "4400" },
	]

	# Return validation data
	return validation_data

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
	print(f"Max column area: {max_column_area}")
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