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

// Capture stop audio click
var interruptClicked = false;
var currentRowIndex = -1;

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

	fieldPageNumber.addEventListener("keypress", onPageNumberKeyPressed);

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
				case "Better Life Pharma Inc - Jan 31 Oct 31 2022.pdf":
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
				case "Tesla - December 31 2020.pdf":
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
	
	// Change page number
	changePageNumber(currentPageNumber + pageDelta);
}

//
// Change page to new number
//
function changePageNumber(newPageNumber) {

	// Only operate if PDF is cached
	if (!cachedPDF) return;

	// Adjust current page
	let oldPageNumber = currentPageNumber;
	if (newPageNumber < 1) {
		newPageNumber = 1;
	}
	else if (newPageNumber > cachedPDF.numPages) {
		newPageNumber = cachedPDF.numPages;
	}

	// No need to re-render if it's the same page
	if (newPageNumber == oldPageNumber) {

		// Enable page controls
		enablePageControls(true);

		// Selectively disable buttons at first/last page
		if (newPageNumber == 1) {
			buttonPreviousPage.disabled = true;
		}
		else if (newPageNumber >= cachedPDF.numPages) {
			buttonNextPage.disabled = true;
		}

		// Don't re-render page
		return;
	}

	// Display new page
	displayTargetPage(cachedPDF, newPageNumber);
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
	pageNum = parseInt(pageNum);
	pdf.getPage(pageNum).then(page => {

		// Render thumbnail
		renderPageToCanvas(page, "pdf-view", 300, false);

		// Render hidden full view
		renderPageToCanvas(page, "image-full-view", 1536, true);

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

		// Download file
		saveObjectAsFile("financial-data." + format, dataObject, format);
	}
	if (format == "csv") {

		// Quote all labels
		dataElements.forEach(row => row["label"] = "\"" + row["label"] + "\"");

		// Join header and data rows
		const array = [Object.keys(dataElements[0])].concat(dataElements);

		// Convert rows to strings
		dataObject = array.map(it => Object.values(it).toString()).join('\n');

		// Download file
		saveObjectAsFile("financial-data." + format, dataObject, format);
	}
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
	let container = document.querySelectorAll("#validation-content row");
	for (rowElement of container) {

		// Skip header row
		if (rowElement.id != "header-row") {

			// Get row label
			let rowLabel = rowElement.dataset.label;

			// Get row value
			let valueField = rowElement.querySelector("input[type='text']");
			let rowValue = "";
			if (valueField) {
				rowValue = valueField.value;
			}

			// Add element to list
			let dataElement = { "label": rowLabel, "value": rowValue }
			dataElements.push(dataElement);
		}
	}

	return dataElements;
}

//
// User interrupted audio playback
//
function interruptAudio(event) {

	// Set interrupt flag
	interruptClicked = true;

	// Stop audio
	let currentAudio = document.querySelector("#audio-" + currentRowIndex);
	if (currentAudio) {

		// Stop audio
		currentAudio.pause();
		currentAudio.currentTime = 0;

		// Reset cell image transforms
		let imageField = document.getElementById("cell-image-" + currentRowIndex);
		imageField.style = "";
	}

	// Call finished handler explicitly
	// (for situations where the audio was interrupted)
	onAudioFinished(currentRowIndex);

	return false;
}

//
// Audio finished playing
//
function onAudioFinished(rowIndex) {
	
	// Check if interrupt was clicked
	if (interruptClicked) {

		// Reset interrupt flag
		interruptClicked = false;

		// Remove interrupt listener
		removeEventListener("mousedown", interruptAudio, true);

		// Focus interrupted field
		let interruptedField = document.querySelector("#audio-" + rowIndex + " ~ input");
		if (interruptedField) {

			// Shade field background
			interruptedField.style.background = "#ffe0e0";
			window.setTimeout(() => interruptedField.style.background = "#ffffff", 1000);

			// Put cursor in field
			interruptedField.select();
			window.setTimeout(() => interruptedField.focus(), 0);
		}
	}
	else {

		// No interrupt, so play next audio
		nextRowId = rowIndex + 1;
		playAudio(nextRowId);
	}
}

//
// Key pressed in page number field
//
function onPageNumberKeyPressed(e) {

	// Only activate on Enter
	if (e.key === "Enter") {
		
		// Get new number
		let newPageNumber = fieldPageNumber.value;

		// Change page number
		changePageNumber(newPageNumber);

		// But don't submit the form
		e.preventDefault();
		return false;
	}
}

//
// User changed field value
//
function onValueChanged(field) {

	// Get the new value
	newValue = field.value;

	// Get row element and row ID
	rowElement = field.parentElement;
	rowId = rowElement.dataset.id;

	// Clear the row's audio
	audioElement = document.getElementById("audio-" + rowId);
	audioElement.dataset.status = "updating";

	// Create temporary form
	let audioChangeForm = document.createElement("form");
	audioChangeForm.method = "POST";
	let formData = new FormData(audioChangeForm);
	formData.append("value-string", newValue);

	// Update audio string
	fetch("/create-audio-string", { method: "POST", body: formData })
		.then(response => response.json())
		.then(responseData => {

			// Update the audio string
			newAudioString = responseData["audio_string"];
			audioElement.src = newAudioString;

			// Clear updating flag
			audioElement.dataset.status = "";
		})
		.catch(error => {
			// Error
			console.log(error);
			window.location.href = "/error.html";
		});
}

//
// Play audio sample
//
function playAudio(rowIndex) {

	// Set interrupt handler
	addEventListener("mousedown", interruptAudio, true);
	currentRowIndex = rowIndex;

	// Clear highlighting and selection from all input fields
	resetTranscribedFields();
	
	// Get control references
	let audioSample = document.getElementById("audio-" + rowIndex)
	let imageField = document.getElementById("cell-image-" + rowIndex);
	if (!audioSample) return;

	// Highlight image field
	imageField.style = "border: 2px solid red; transform: scale(1.4);";

	// Check for updating audio
	if (audioSample.dataset.status == "updating") {

		// Wait for update to finish
		window.setTimeout(() => playAudio(rowIndex), 500);
	}
	
	// Unhighlight field on audio end
	audioSample.onended = () => {
		imageField.style = "";
	}

	// Set finished event handler
	audioSample.addEventListener("ended", () => onAudioFinished(rowIndex), false);

	// Play the audio
	audioSample.play();

	// Don't execute default action if invoked directly
	return false;
}

//
// Populate validation data
//
async function populateValidationData(response) {

	// Convert response to json data
	let jsonData = await response.json();
	let validationData = jsonData["validation_data"];

	// Get control references
	let container = document.getElementById("validation-content")

	// No validation data
	if (!validationData || validationData.length == 0) {

		// Remove section content
		let contentRows = document.querySelectorAll("#validate-results .category row");
		if (contentRows) {
			for (let contentRow of contentRows) {
				contentRow.remove();
			}
		}

		// Display informative message
		let messageHtml = `
		<row id="header-row" class="header-row">
			<p>Sorry, the page did not contain any recognizable table data. Please select another page and try again.</p>
		</row>
		`;
		let messageElement = document.createElement("template")
		messageElement.innerHTML = messageHtml;
		container.appendChild(messageElement.content);
	
		// Disable next button
		let nextButton = document.getElementById("button-next-validate");
		nextButton.disabled = true;

		return;
	}

	// Add row headers
	let headerHtml = `
	<row id="header-row" class="header-row">
		<span class="line-item-label">&nbsp;</span>
		<span class="header-label">Original Value</span>
		<span class="header-label">Extracted Value</span>
	</row>
	`;
	let headerElement = document.createElement("template")
	headerElement.innerHTML = headerHtml;
	container.appendChild(headerElement.content);

	// Render rows
	for (const [i, row] of validationData.entries()) {

		// Define row HTML
		let rowHtml = `
		<row id="row-${i}" class="validation-row" data-id=${i} data-label="${row.label}">
			<span class='line-item-label'>${row.label}</span>
			<img id="cell-image-${i}" src="${row.cell_image}" class="cell-image">
			<button id="btn-play" type="button" title="Play" onclick="playAudio(${i})" ${row.audio ? "" : "disabled"}><img src="/static/images/speaker.png"></button>
			<audio id="audio-${i}" autobuffer="autobuffer" src="${row.audio}"></audio>
			<input type="text" value="${row.extracted_value}" onchange="onValueChanged(this)">
			<button id="btn-delete" type="button" title="Delete" onclick="deleteRow(${i})"><img src="/static/images/delete.png"></button>
		</row>
		`;

		// Create row element
		let rowElement = document.createElement("template");
		rowElement.innerHTML = rowHtml;

		// Add row to container
		container.appendChild(rowElement.content);
	}

	// Append row count
	let rowCount = document.createElement("template");
	rowCount.innerHTML = `<span>${validationData.length} rows</span>`;
	container.appendChild(rowCount.content);
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
// Reset formatting on transcribed fields
//
function resetTranscribedFields() {

	// Get field container
	inputFields = document.querySelectorAll("#validation-content-2 input");

	// Reset input fields
	for (inputField of inputFields) {
		inputField.style = "";
		inputField.blur();
	}
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
function saveObjectAsFile(filename, dataObject, format) {
	
	dataObject = "\uFEFF" + dataObject;

	const blob = new Blob([dataObject], { type: "text/" + format, encoding: "UTF-8" });
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

		// Successful
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