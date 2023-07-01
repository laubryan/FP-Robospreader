//
// Home
//

// Globals
var cachedPDF = null;
var currentPageNumber = 0;

var buttonPreviousPage = null;
var buttonNextPage = null;
var buttonNextSelect = null;
var buttonNextValidate = null;
var fieldPageNumber = null;

//
// Accept validations
//
function acceptValidation() {

	// Update page state
	updatePageState(3);
}

//
// Browse for file
//
function browseForFile() {

	// Assign control references
	buttonPreviousPage = document.getElementById("button-previous");
	buttonNextPage = document.getElementById("button-next");
	fieldPageNumber = document.getElementById("page-number");
	buttonNextSelect = document.getElementById("button-next-select");
	buttonNextValidate = document.getElementById("page-next-validate");

	// Get and click file control
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

			// DEBUG
			switch (filename) {
				case "407 International - March 31 2021.pdf":
					renderDocument(fileURI, 2);
					return;
				case "Air Canada - December 31 2019.pdf":
					renderDocument(fileURI, 10);
					return;
				case "BCE - Financial Report - 2020-2022.pdf":
					renderDocument(fileURI, 83);
					return;
				case "Better Life Pharama Inc - Jan 31 Oct 31 2022.pdf":
					renderDocument(fileURI, 3);
					return;
				case "NextGen Food Robotics Corp - 2022-04-30 - 2023-01-31..pdf":
					renderDocument(fileURI, 3);
					return;
				case "Rogers - Q1-2020.pdf":
					renderDocument(fileURI, 4);
					return;
				case "Starbucks - Annual Report - 2020.pdf":
					renderDocument(fileURI, 54);
					return;
			}

			// Render document
			renderDocument(fileURI);
		}
	}
}

//
// Change page using delta
//
function changePageDelta(pageDelta) {

	// Only operate if PDF is cached
	if (!cachedPDF) return;

	// Disable page controls
	enablePageControls(false);
	
	// Adjust current page
	let oldPageNumber = currentPageNumber;
	currentPageNumber += pageDelta;
	if (currentPageNumber < 1) {
		currentPageNumber = 1;
	}
	else if (currentPageNumber > cachedPDF.numPages) {
		currentPageNumber = cachedPDF.numPages;
	}

	// No need to re-render if it's the same page
	if (currentPageNumber == oldPageNumber) {

		// Enable page controls
		enablePageControls(true);

		// Selectively disable buttons at first/last page
		if (currentPageNumber == 1) {
			buttonPreviousPage.disabled = true;
		}
		else if (currentPageNumber >= cachedPDF.numPages) {
			buttonNextPage.disabled = true;
		}

		// Don't re-render page
		return;
	}

	// Display new page
	displayTargetPage(cachedPDF, currentPageNumber);
}

//
// Delete validation row
//
function deleteRow(rowId) {

	// Search for row
	let container = document.getElementById("validation-content");
	let targetId = "row-" + rowId;
	for (rowElement of container.children) {

		// Delete the matching row
		if (rowElement.id == targetId) {
			container.removeChild(rowElement);
			return;
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
// Display the target page
//
function displayTargetPage(pdf, pageNum) {

	// Get the page
	pdf.getPage(pageNum).then(page => {

		// Render thumbnail
		renderPageToCanvas(page, "pdf-view", 300, false);

		// Render hidden full view
		renderPageToCanvas(page, "image-full-view", 1024, true);

		// Display current page number
		currentPageNumber = pageNum;
		fieldPageNumber.value = pageNum;
	});
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
// Enable/disable page controls
//
function enablePageControls(enable) {
	buttonPreviousPage.disabled = !enable;
	buttonNextPage.disabled = !enable;
	fieldPageNumber.disabled = !enable;
	buttonNextSelect.disabled = !enable;
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
		<row id="row-${i}" class="validation-row" data-index="row-${i}" data-label="${row.label}">
			<span class='line-item-label'>${row.label}</span>
			<img src="${row.cell_image}" class="cell-image">
			<button id="btn-play" type="button" title="Play"><img src="/static/images/play.png"></button>
			<input type="number" value="${row.extracted_value}">
			<button id="btn-delete" type="button" title="Delete" onclick="deleteRow(${i})"><img src="/static/images/delete.png"></button>
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
function renderDocument(filename, pageNum=1) {

	// Load PDF
	let loadingTask = pdfjsLib.getDocument(filename);
	loadingTask.promise.then(pdf => {

		// Cache loaded PDF
		cachedPDF = pdf;

		// Display number of pages
		displayNumPages(pdf.numPages);
		
		// Display target page
		displayTargetPage(pdf, pageNum);
	});
}

//
// Render page to canvas
//
function renderPageToCanvas(page, canvasId, renderWidthPx, saveBuffer) {

	// Initialize viewport
	let viewport = page.getViewport({ scale: 1 });
	let scale = renderWidthPx / viewport.width;
	let outputScale = window.devicePixelRatio || 1;
	let scaledViewport = page.getViewport({ scale: scale });
	let canvas = document.getElementById(canvasId);
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

		// Save image data to field
		if (saveBuffer) {

			// Convert canvas image to string
			let dataUri = canvas.toDataURL("image/png");

			// Save image data to field
			let bufferField = document.getElementById("image-buffer");
			bufferField.value = dataUri;

			// Enable page controls
			enablePageControls(true);
		}
	});
}

//
// Reset select page state
//
function resetSelectPage() {

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
	pageNumberField.value = "0";

	// Reset page controls
	enablePageControls(false);
}

//
// Reset validation page state
//
function resetValidationPage() {

	// Validation Rows
	let container = document.getElementById("validation-content");
	container.innerHTML = "";
}

//
// Reset and restart
//
function restart(resetSelect, resetValidation) {

	// Reset select page state
	if (resetSelect) {
		resetSelectPage();
	}

	// Reset validation page state
	if (resetValidation) {
		resetValidationPage();
	}

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

	// Display working page
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

			// Display validation page
			updatePageState(2);
		}
		else {
			// Error
			console.log(response);
			window.location.href = "/error.html";
		}
	}).catch(error => {
		// Error
		console.log(response);
		window.location.href = "/error.html";
	});
}

//
// Update visible page sections
//
function updatePageState(visibleSectionIndex) {

	// Get section references
	let sections = [
		document.getElementById("choose-page"),
		document.getElementById("working-page"),
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