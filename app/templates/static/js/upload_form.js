async function uploadReportData() {
    const formData = new FormData();
    formData.append("documentNo", document.getElementById("documentNo").value);
    formData.append("documentType", document.getElementById("documentType").value);
    formData.append("subjectDocument", document.getElementById("subjectDocument").value);
    formData.append("documentDesc", document.getElementById("documentDesc").value);
    formData.append("m_tv_broad", document.getElementById("model_tv").value);
    
    // Get the selected options from the <select> element
    const selectedOptions = Array.from(document.querySelectorAll("#distributed_to option:checked")).map(option => option.value).join(";");
    
    // Append the selected options as an array
    formData.append("distributed_to", JSON.stringify(selectedOptions));

    formData.append("filenameUpload", document.getElementById("uploadFile").files[0]);

    try {
        const response = await fetch('/app/document/upload/upload_report', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            // Handle a successful response
            console.log(data.message); // or perform any other actions
        } else {
            // Handle an error response
            console.error('Failed to upload data');
        }
    } catch (error) {
        console.error('Error occurred:', error);
    }
}
