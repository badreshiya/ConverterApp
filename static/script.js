document.addEventListener("DOMContentLoaded", function () {
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");
    const convertButton = document.getElementById("convertButton");
    const statusMessage = document.getElementById("statusMessage");
    const progressBar = document.getElementById("progressBar").querySelector("div");
    const spinner = document.getElementById("spinner");

    let selectedFile = null;
    let downloadURL = null;

    function resetUI() {
        progressBar.style.width = "0%";
        progressBar.parentElement.style.display = "none";
        spinner.style.display = "none";
        convertButton.textContent = "Convert to Excel";
        convertButton.disabled = true;
        convertButton.onclick = startUpload;
        downloadURL = null;
        fileInput.value = "";
        statusMessage.textContent = "";
    }

    function startUpload() {
        if (!selectedFile) {
            statusMessage.textContent = "Please select a file first.";
            statusMessage.style.color = "red";
            return;
        }

        resetUI();
        statusMessage.textContent = "Converting...";
        progressBar.parentElement.style.display = "block";
        spinner.style.display = "block";
        convertButton.disabled = true;

        const formData = new FormData();
        formData.append("file", selectedFile);

        fetch("/upload", {
            method: "POST",
            body: formData,
            headers: { Accept: "application/json" },
        })
            .then((response) => response.json())
            .then((data) => {
                spinner.style.display = "none";
                progressBar.style.width = "100%";

                if (data.file_path) {
                    downloadURL = data.file_path;
                    convertButton.textContent = "Download Converted File";
                    convertButton.onclick = downloadFile; // Fix: Ensure downloadFile is called
                    convertButton.disabled = false;
                    statusMessage.textContent = "Conversion successful!";
                    statusMessage.style.color = "green";
                } else {
                    statusMessage.textContent = data.error || "Conversion failed!";
                    statusMessage.style.color = "red";
                    convertButton.textContent = "Convert to Excel"; // Reset button text on failure
                    convertButton.onclick = startUpload;
                    convertButton.disabled = false;
                }
            })
            .catch((error) => {
                console.error("Error:", error);
                statusMessage.textContent = "Error: " + error.message;
                statusMessage.style.color = "red";
                spinner.style.display = "none";
                progressBar.parentElement.style.display = "none";
                convertButton.disabled = false;
            });
    }

    function downloadFile() {
        if (!downloadURL) {
            statusMessage.textContent = "No file available for download.";
            statusMessage.style.color = "red";
            return;
        }

        // ✅ Force file download instead of just opening it
        const a = document.createElement("a");
        a.href = downloadURL;
        a.download = downloadURL.split("/").pop(); // Get file name from URL
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        statusMessage.textContent = "Download completed.";
        statusMessage.style.color = "green";

        // Reset UI after 3 seconds
        setTimeout(resetUI, 3000);
    }

    // ✅ Enable Clicking on Drop Zone to Open File Dialog
    dropZone.addEventListener("click", () => fileInput.click());

    // ✅ Handle File Selection
    fileInput.addEventListener("change", () => {
        selectedFile = fileInput.files[0];
        statusMessage.textContent = "File selected: " + selectedFile.name;
        statusMessage.style.color = "blue";
        convertButton.disabled = false;
    });

    // ✅ Handle Drag & Drop Functionality
    dropZone.addEventListener("dragover", (event) => {
        event.preventDefault();
        dropZone.style.borderColor = "lightblue";
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.style.borderColor = "";
    });

    dropZone.addEventListener("drop", (event) => {
        event.preventDefault();
        dropZone.style.borderColor = "";

        if (event.dataTransfer.files.length > 0) {
            selectedFile = event.dataTransfer.files[0];
            statusMessage.textContent = "File selected: " + selectedFile.name;
            statusMessage.style.color = "blue";
            convertButton.disabled = false;
        }
    });

    convertButton.addEventListener("click", startUpload);
});
