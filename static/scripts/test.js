//
// Test Page Functions
//

// Capture stop audio click
var interruptClicked = false;
var currentRowIndex = -1;

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
		removeEventListener("mousedown", interruptAudio);

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
// Play audio sample
//
function playAudio(rowIndex) {

	// Set interrupt handler
	addEventListener("mousedown", interruptAudio, true);
	currentRowIndex = rowIndex;

	// Clear highlighting and selection from all input fields
	inputFields = document.querySelectorAll("#validation-content input");
	for (inputField of inputFields) {
		inputField.style = "";
		inputField.blur();
	}

	// Get control references
	let audioSample = document.getElementById("audio-" + rowIndex)
	let imageField = document.getElementById("cell-image-" + rowIndex);
	if (!audioSample) return;

	// Highlight image field
	imageField.style = "border: 2px solid red; transform: scale(1.4);";

	// Unhighlight field on audio end
	audioSample.onended = () => {
		imageField.style = "";
	}

	// Set finished event handler
	audioSample.addEventListener("ended", () => onAudioFinished(rowIndex), false);

	// Play the audio
	audioSample.play();
//
// Record test results
//
function recordTestResults(elapsedSeconds, numValues, numErrors, nextPageState) {

	fetch("/record-test-results", { method: "POST", body: formData }).then(response => {
		if (response.ok) {
			// Success
			// Display validation page
			updatePageState(nextPageState);
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
}

//
// Update visible page sections
//
function updatePageState(visibleSectionIndex) {

	// Set all section visibilities
	for (let i = 1; i <= 6; i++) {

		// Get section reference
		let section = document.getElementById("validation-test-" + i);

		// Hide section if not indicated
		if (i != visibleSectionIndex) {
			section.style.display = "none";
		}
		else {
			// Show indicated section
			section.style.display = "block";
		}
	}
}