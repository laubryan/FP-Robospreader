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
	print(f"Image dimensions: {page_width} x {page_height} x {page_depth}")

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

	return binarized_array# Segment table
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