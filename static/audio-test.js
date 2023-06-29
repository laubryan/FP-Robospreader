//
// Audio Test
//

let startTimes = {};

//
// Start test
//
function startTest(language) {
	console.log("Starting Test");

	// Disable controls
	$("button").prop("disabled", true);

	// Clear any existing table
	let resultsSection = document.getElementById("test-results");
	resultsSection.textContent = "";

	// Run English test
	if (language == "English" || language == "all languages") {
		startLanguageTest("Normal", "English");
	}

	// Run Spanish test
	if (language == "Spanish" || language == "all languages") {
		startLanguageTest("Normal", "Spanish");
	}

	// Run Italian test
	if (language == "Italian" || language == "all languages") {
		startLanguageTest("Normal", "Italian");
	}

	// Run Sentences test
	if (language == "Sentences") {
		startLanguageTest("Sentences", "English");
	}

	// Run Vosk test
	if (language == "Vosk") {
		startLanguageTest("Vosk", "English");
	}

	// Run PocketSphinx test
	if (language == "PocketSphinx") {
		startLanguageTest("PocketSphinx", "English");
	}
}

//
// Start individual language test
//
function startLanguageTest(testType, language) {

	// Define strings
	languageLower = language.toLowerCase();

	// Add table
	let resultsSection = document.getElementById("test-results");
	resultsSection.innerHTML +=
	`
	<section class="category">
		<h2>${language} Results ${ testType == "Normal" ? "" : "(" + testType + ")" }</h2>
		<table>

			<thead>
				<tr>
					<th>Language</th>
					<th>File</th>
					<th>Baseline WER</th>
					<th>Tested WER</th>
				</tr>
			</thead>

			<tbody id="result-rows-${languageLower}">
				<tr>
					<td class="cell-status" colspan="4">Running ${language} tests...</td>
				</tr>
			</tbody>

			<tfoot>
				<tr>
					<th scope="row">Baseline Average WER</th>
					<td id="baseline-average-wer-${languageLower}" class="cell-value"></td>
					<th scope="row">Tested Average WER</th>
					<td id="average-wer-${languageLower}" class="cell-value"></td>
				</tr>
			</tfoot>

		</table>
	</section>
	`;

	$.ajax({
		type: "POST",
		url: "/api/evaluate-language",
		data: {
			type: testType,
			language: language
		},
		success: onTestFinished,
		error: onTestError
	});
}

//
// Test finished
//
function onTestFinished(results) {

	// Initialize variables
	language = results[0].language.toLowerCase();
	totalBaselineWER = 0;
	totalWER = 0;

	// Get DOM references
	let resultsSection = document.getElementById(`result-rows-${language}`);
	let werBaselineSection = document.getElementById(`baseline-average-wer-${language}`);
	let werSection = document.getElementById(`average-wer-${language}`);

	// Clear table rows
	resultsSection.textContent = "";

	// Build results output
	for (result of results) {

		// Create row
		let row = document.createElement("tr");

		// Create fields

		// Language
		let languageField = document.createElement("td");
		let languageText = document.createTextNode(result.language);
		languageField.appendChild(languageText);

		// File
		let audioFile = document.createElement("td");
		let audioText = document.createTextNode(result.filename);
		audioFile.appendChild(audioText);

		// Baseline WER
		let defaultWer = document.createElement("td");
		let defaultWerText = document.createTextNode(result.baseline_wer);
		defaultWer.classList.add("cell-value");
		defaultWer.appendChild(defaultWerText);
		defaultWer.title = result.reference_text;
		totalBaselineWER += result.baseline_wer;

		// Fitered WER
		let filteredWer = document.createElement("td");
		let filteredWerText = document.createTextNode(result.best_wer);
		filteredWer.classList.add("cell-value");
		filteredWer.title = result.best_text;
		filteredWer.appendChild(filteredWerText);
		totalWER += result.best_wer;

		// Assemble row
		row.appendChild(languageField);
		row.appendChild(audioFile);
		row.appendChild(defaultWer);
		row.appendChild(filteredWer);

		// Add row
		resultsSection.appendChild(row);
	}

	// Calculate WER statistics
	let averageBaselineWER = totalBaselineWER / results.length
	let averageWER = totalWER / results.length
	werSection.textContent = Math.round(averageWER * 100) / 100;
	werBaselineSection.textContent = Math.round(averageBaselineWER * 100) / 100;

	// Enable controls
	$("button").prop("disabled", false);
}

//
// Test error
//
function onTestError() {
	console.log("Failed");
}