//
// Home
//

function browseForFile() {
	let fileControl = document.getElementById("file-control");
	fileControl.click();
	fileControl.onchange = () => {
		let fileLabel = document.getElementById("file-name");
		fileLabel.innerText = fileControl.files[0].name;
	}
}