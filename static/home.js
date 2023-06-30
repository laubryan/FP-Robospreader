//
// Home
//

//
// Accept validations
//
function acceptValidation() {

	// Update page state
	updatePageState(2);
}

//
// Browse for file
//
function browseForFile() {
	let fileControl = document.getElementById("file-control");
	fileControl.click();
	fileControl.onchange = () => {

		// Get the selected file
		let pdfFile = fileControl.files[0];

		if (pdfFile) {

			// Create URI
			fileURI = URL.createObjectURL(pdfFile);

			// Display file data

			// Filename
			let filename = fileControl.files[0].name;
			displayFilename(filename);

			// Render document
			renderDocument(fileURI);
		}
	}
}

//
// Display filename
//
function displayFilename(filename) {

	// Filename
	let fileLabel = document.getElementById("file-name");
	fileLabel.innerText = filename;
}

//
// Display number of pages
//
function displayNumPages(numPages) {
	let numPagesControl = document.getElementById("num-pages");
	numPagesControl.innerText = numPages;
}

//
// Download data as format
//
function downloadData(format) {

	// Get raw data
	let dataElements = getValidatedData();
	format = format.toLowerCase();
	
	// Download data format
	if (format == "json") {
		dataObject = JSON.stringify(dataElements);
	}
	if (format == "csv") {
		const array = [Object.keys(dataElements[0])].concat(dataElements);
		dataObject = array.map(it => Object.values(it).toString()).join('\n');
	}
	saveObjectAsFile("financial-data." + format, dataObject);
}

//
// Get validated data
//
function getValidatedData() {

	// Assemble validated data
	let dataElements = [];
	let container = document.getElementById("validation-content");
	for (rowElement of container.children) {

		// Get row label
		let rowLabel = rowElement.dataset.label;

		// Get row value
		let valueField = rowElement.querySelector("input[type='number']");
		let rowValue = valueField.value;

		// Add element to list
		let dataElement = { "label": rowLabel, "value": rowValue }
		dataElements.push(dataElement);
	}

	return dataElements;
}

//
// Populate validation data
//
async function populateValidationData(response) {

	// Convert response to json data
	let jsonData = await response.json();
	let validationData = jsonData["validation_data"];

	// Render rows
	let container = document.getElementById("validation-content")
	for (const[i, row] of validationData.entries()) {

		// Define row HTML
		let rowHtml = `
		<row class="validation-row" data-index="row-${i}" data-label="${row.label}">
			<span class='line-item-label'>${row.label}</span>
			<img src="/static/images/debug-field-value.png">
			<button id="btn-back" class="button-playback" title="RW"><img src="/static/images/play.png"></button>
			<input type="number" value="${row.extracted_value}">
			<input type="checkbox">
		</row>
		`;

		// Create row element
		let rowElement = document.createElement("template");
		rowElement.innerHTML = rowHtml;

		// Add row to container
		container.appendChild(rowElement.content);
	}
}

//
// Render PDF document
//
function renderDocument(filename) {

	// Load PDF
	let loadingTask = pdfjsLib.getDocument(filename);
	loadingTask.promise.then(pdf => {

		// Display number of pages
		displayNumPages(pdf.numPages);
		
		// Load target page
		pdf.getPage(10).then(page => {

			// Initialize viewport
			let renderWidthPx = 300;
			let viewport = page.getViewport({ scale: 1 });
			let scale = renderWidthPx / viewport.width;
			let outputScale = window.devicePixelRatio || 1;
			let scaledViewport = page.getViewport({ scale: scale });
			let canvas = document.getElementById("pdf-view");
			let context = canvas.getContext("2d");

			// Initialize canvas dimensions
			canvas.width = Math.floor(scaledViewport.width * outputScale);
			canvas.height = Math.floor(scaledViewport.height * outputScale);
			canvas.style.width = Math.floor(scaledViewport.width) + "px";
			canvas.style.height = Math.floor(scaledViewport.height) + "px";

			// Define transform
			let transform = outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : null;

			// Create render context
			let renderContext = {
				canvasContext: context,
				transform: transform,
				viewport: scaledViewport
			};

			// Render page
			let renderTask = page.render(renderContext);
			renderTask.promise.then(() => {

				// Convert canvas image to string
				let dataUri = canvas.toDataURL("image/png");

				// Save image data to field
				let bufferField = document.getElementById("image-buffer");
				bufferField.value = dataUri;
			});
		});
	});
}

//
// Reset and restart
//
function restart() {

	// Reset controls

	// File control
	let fileControl = document.getElementById("file-control");
	fileControl.value = "";

	// Filename
	displayFilename("No file selected");

	// Pages
	displayNumPages("-");

	// Canvas
	let canvas = document.getElementById("pdf-view");
	let context = canvas.getContext("2d");
	context.clearRect(0, 0, canvas.width, canvas.height);

	// Page number
	let pageNumberField = document.getElementById("page-number");
	pageNumberField.value = "99";

	// Validation Rows
	let container = document.getElementById("validation-content");
	container.innerHTML = "";

	// Update page state
	updatePageState(0);
}

//
// Save object as file
//
function saveObjectAsFile(filename, dataObject) {
	
	const blob = new Blob([dataObject], { type: "text/json" });
	const link = document.createElement("a");

	link.download = filename;
	link.href = window.URL.createObjectURL(blob);
	link.dataset.downloadurl = ["text/json", link.download, link.href].join(":");

	const evt = new MouseEvent("click", {
			view: window,
			bubbles: true,
			cancelable: true,
	});

	link.dispatchEvent(evt);
	link.remove()
}

//
// Submit the selected page
//
async function submitPage() {

	// Update page state
	updatePageState(1);

	// Get form object for submission
	let pageForm = document.getElementById("choose-page-form");
	let formData = new FormData(pageForm);

	// Get the image buffer data
	let bufferField = document.getElementById("image-buffer");
	let imageData = bufferField.value;
	
	// Add the image buffer to the form data
	formData.append("page_image", imageData);

	// Submit the form
	fetch("/process-page-image", { method: "POST", body: formData }).then(response => {
		if (response.ok) {
			// Success
			populateValidationData(response);
		}
	}).catch(error => {
		// Error
		console.log("Error");
		console.log(response);
	});
}

//
// Update visible page sections
//
function updatePageState(visibleSectionIndex) {

	// Get section references
	let sections = [
		document.getElementById("choose-page"),
		document.getElementById("validate-results"),
		document.getElementById("download-data"),
	];

	// Hide all sections
	for (section of sections) {
		section.style.display = "none";
	}

	// Show the target section
	sections[visibleSectionIndex].style.display = "block";
}