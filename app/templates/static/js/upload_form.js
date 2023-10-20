async function uploadReportData() {
    const formData = new FormData();
    formData.append("documentNo", document.getElementById("documentNo").value);
    formData.append("documentType", document.getElementById("documentType").value);
    formData.append("subjectDocument", document.getElementById("subjectDocument").value);
    formData.append("documentDesc", document.getElementById("documentDesc").value);
    formData.append("m_tv_broad", document.getElementById("model_tv").value);
    formData.append("filenameUpload", document.getElementById("uploadFile").files[0]);

    const server_respon = document.getElementById("server_response");

    try {
        const response = await fetch('/app/document/upload/upload_report', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            // Handle a successful response
            console.log(data.message); // or perform any other actions
            server_respon.innerText = data.message;
        } else {
            // Handle an error response
            console.error('Failed to upload data');
            server_respon.innerText = data.message;
        }
    } catch (error) {
        console.error('Error occurred:', error);
    }
}

