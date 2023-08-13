//
// Test Page Functions
//

//
// Play audio sample
//
function playAudio(rowIndex) {

	// Get control references
	let audioSample = document.getElementById("audio-" + rowIndex)
	let imageField = document.getElementById("cell-image-" + rowIndex);

	// Highlight image field
	imageField.style = "border: 2px solid red; transform: scale(1.4);";

	// Unhighlight field on audio end
	audioSample.onended = () => {
		imageField.style = "";
	}

	// Play the audio
	audioSample.play();
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