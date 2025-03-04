document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');  // Get the upload button
    const statusMessage = document.getElementById('statusMessage');
    const progressBar = document.getElementById('progressBar').querySelector('div');  // Correctly select the inner div
    const spinner = document.getElementById('spinner');
    const downloadLink = document.getElementById('downloadLink');


    function uploadFile(file) {
        if (!file || file.type !== "application/json") {
            statusMessage.textContent = "Please upload a valid JSON file.";
            statusMessage.style.color = "red";
            return;
        }

        statusMessage.textContent = '';
        statusMessage.style.color = '';
        progressBar.style.width = '0%';
        progressBar.parentElement.style.display = 'block'; // Show the progress bar container
        spinner.style.display = 'block';

        const formData = new FormData();
        formData.append('file', file);

        fetch('/', {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json'  // Crucial: Tell the server we expect JSON
            }
        })
        .then(response => {
            // Check for HTTP errors *before* parsing JSON
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Server error');
                }).catch(() => { // Handle non-JSON error responses
                    throw new Error('Server error');
                });
            }
            return response.json(); // Only parse JSON if successful
        })
        .then(data => {
             spinner.style.display = 'none';
             progressBar.style.width = '100%';

             if (data.download_url) { //Changed: use download_url
                // Display S3 URL.
                downloadLink.href = data.download_url; //Changed: use download_url
                downloadLink.textContent = 'Download from S3';
                downloadLink.style.display = 'block'; // Make link visible
                downloadLink.target = "_blank"; // Open in a new tab/window
                statusMessage.textContent = 'Conversion successful! File uploaded to S3.';
                statusMessage.style.color = 'green';

             }
             else {
                //Should not reach here, handled via error.
                statusMessage.textContent = 'Conversion successful! But failed to display S3 URL';
                statusMessage.style.color = 'green';
                downloadLink.style.display = 'none';
             }

        })
        .catch(error => {
            console.error('Error:', error);
            statusMessage.textContent = `Error: ${error.message}`; // Show specific error
            statusMessage.style.color = 'red';
            spinner.style.display = 'none';
            progressBar.parentElement.style.display = 'none';
        });
    }



    // Event Listeners

    // 1. Drag and Drop Events
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files; // Set the file input's files
            uploadFile(files[0]);    // Automatically upload
        }
    });

    // 2. File Input Change Event
    fileInput.addEventListener('change', (e) => {
        if (fileInput.files.length > 0) {
            uploadFile(fileInput.files[0]); // Upload selected file
        }
    });

    // 3. Click event on the dropZone to trigger file input
    dropZone.addEventListener('click', () => {
        fileInput.click(); // Programmatically click the hidden file input
    });

    // 4. Upload Button (Optional - if you want a separate button)
    if (uploadButton) { // Check if uploadButton exists
        uploadButton.addEventListener('click', () => {
           if (fileInput.files.length > 0) {
              uploadFile(fileInput.files[0]);
            } else {
              statusMessage.textContent = "Please select a file first.";
              statusMessage.style.color = "red";
            }
        });
    }

});