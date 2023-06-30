//
// Home
//

//
// Browse for file
//
function browseForFile() {
	let fileControl = document.getElementById("file-control");
	fileControl.click();
	fileControl.onchange = () => {

		// Get the selected file
		let fileLabel = document.getElementById("file-name");
		let pdfFile = fileControl.files[0];

		if (pdfFile) {

			// Create URI
			fileURI = URL.createObjectURL(pdfFile);

			// Display filename in control
			let filename = fileControl.files[0].name;
			fileLabel.innerText = filename;

			// Render document
			renderDocument(fileURI);
		}
	}
}

//
// Test
//
function renderDocument(filename) {

	// Load PDF
	let loadingTask = pdfjsLib.getDocument(filename);
	loadingTask.promise.then(pdf => {

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
				let dataUri = canvas.toDataURL("image/png");
				console.log(dataUri);
			});
		});
	});
}