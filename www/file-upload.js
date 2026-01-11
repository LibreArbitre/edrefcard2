// EDRefCard - File Upload Enhancement
// Handles drag-and-drop file upload functionality

//Prevent default drag-and-drop behavior on the entire document
// This prevents the browser from opening files when dropped outside the drop zone
document.addEventListener('DOMContentLoaded', () => {
    // Prevent default drag/drop behavior on document
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // File upload functionality
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileupload');

    if (!dropZone || !fileInput) {
        console.error('File upload elements not found');
        return;
    }

    // Highlight drop zone when dragging over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
    });

    // Remove highlight when leaving drop zone
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
        });
    });

    // Handle file drop
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFileLabel(files[0].name);
        }
    });

    // Handle file selection via click
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            updateFileLabel(e.target.files[0].name);
        }
    });

    // Update label to show selected filename
    function updateFileLabel(filename) {
        const textElement = dropZone.querySelector('.file-upload-text');
        if (textElement) {
            textElement.innerHTML = '<strong>Selected:</strong> ' + filename;
        }
    }
});
