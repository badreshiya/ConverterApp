document.addEventListener("DOMContentLoaded", function () {
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");
    const uploadButton = document.getElementById("uploadButton");
    const statusMessage = document.getElementById("statusMessage");
    const downloadLink = document.getElementById("downloadLink");
    const progressBar = document.getElementById("progressBar");
    const progressBarFill = progressBar.querySelector("div");
    const spinner = document.getElementById("spinner");

    // File validation
    const isValidFile = (file) => {
        return file && file.name.toLowerCase().endsWith(".json");
    };

    // Drag & drop handlers
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "#4ade80";
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.style.borderColor = "rgba(255, 255, 255, 0.6)";
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "rgba(255, 255, 255, 0.6)";
        const file = e.dataTransfer.files[0];
        
        if (isValidFile(file)) {
            fileInput.files = e.dataTransfer.files;
            statusMessage.textContent = `Selected: ${file.name}`;
            statusMessage.style.color = "#ffffff";
        } else {
            statusMessage.textContent = "Please drop a valid JSON file";
            statusMessage.style.color = "#ff6b6b";
        }
    });

    // Click handler
    dropZone.addEventListener("click", () => fileInput.click());

    // File input handler
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            if (isValidFile(file)) {
                statusMessage.textContent = `Selected: ${file.name}`;
                statusMessage.style.color = "#ffffff";
            } else {
                statusMessage.textContent = "Invalid file type. Only JSON allowed";
                statusMessage.style.color = "#ff6b6b";
                fileInput.value = "";
            }
        }
    });

    // Upload handler
    uploadButton.addEventListener("click", async () => {
        if (!fileInput.files.length) {
            statusMessage.textContent = "Please select a file first";
            statusMessage.style.color = "#ff6b6b";
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append("jsonFiles", file);

        // UI updates
        progressBar.style.display = "block";
        spinner.style.display = "block";
        progressBarFill.style.width = "0%";

        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            progressBarFill.style.width = "100%";
            statusMessage.textContent = "Conversion completed!";
            statusMessage.style.color = "#4ade80";

            if (data.files?.[0]?.download_url) {
                downloadLink.innerHTML = `
                    <a href="${data.files[0].download_url}" download 
                       class="download-btn">
                        Download ${data.files[0].filename}
                    </a>
                `;

                // Auto-clear download link after 5 minutes
                setTimeout(() => {
                    downloadLink.innerHTML = "";
                    statusMessage.textContent = "Ready for new conversion";
                    statusMessage.style.color = "#ffffff";
                }, 300000);
            }
        } catch (error) {
            console.error("Upload error:", error);
            statusMessage.textContent = `Error: ${error.message}`;
            statusMessage.style.color = "#ff6b6b";
        } finally {
            setTimeout(() => {
                progressBar.style.display = "none";
                spinner.style.display = "none";
            }, 1000);
            fileInput.value = "";
        }
    });
});