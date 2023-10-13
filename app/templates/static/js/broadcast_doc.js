async function populateDocumentNumber() {
    try {
        const documentNumber = document.getElementById("documentNumber");

        // Send an AJAX request to fetch the data
        const response = await fetch('/app/api/function/data');
        if (!response.ok) {
            throw new Error('Failed to fetch data from the server');
        }

        const responseJson = await response.json();
        const registeredData = responseJson.registered_data;

        // Create the select element
        const select = document.createElement("select");
        select.id = "documentNumber";  // Set the id if not already set
        select.className = "form-select";

        // Create an initial default option
        const defaultOption = document.createElement("option");
        defaultOption.value = "";  // Set the value for the default option
        defaultOption.text = "Select a Document Number";
        select.appendChild(defaultOption);

        // Create options based on the registered_data array
        registeredData.forEach(item => {
            const opt = document.createElement("option");
            opt.value = item;
            opt.text = item;
            select.appendChild(opt);
        });

        // Replace the existing documentNumber element with the new select element
        documentNumber.replaceWith(select);

        // Add a change event listener to the select element
        select.addEventListener('change', function() {
            showDetailData(select.value);
        });
    } catch (error) {
        console.error("Error fetching data from the server:", error);
    }
}


async function showDetailData(docnum) {
    const docDetail = document.getElementById("selectedDocumentDetail");
    const ppRecipients = document.getElementById("recipients_category");

    try {
        const response = await fetch(`/app/api/function/data/documents?document_number=${docnum}`);
        if (!response.ok) {
            throw new Error("Failed to fetch data from the server");
        }

        const responseJson = await response.json();
        const contentData = responseJson.content_data;
        const recipientList = responseJson.recipients;
        console.log(recipientList);
        
        // Define labels for the keys
        const labels = {
            document_no: "Document Number",
            document_type: "Document Type",
            model_tv: "TV Model",
            datetime_upload: "Upload At",
            distributed_to: "Distribute To"
        };

        // Clear existing content in docDetail
        docDetail.innerHTML = "";

        // Create an unordered list (ul)
        const ul = document.createElement("ul");

        // Loop through the content_data object's properties and use labels
        for (const key in labels) {
            if (labels.hasOwnProperty(key) && contentData[key]) {
                const li = document.createElement("li");
                li.textContent = `${labels[key]}: ${contentData[key]}`;
                ul.appendChild(li);
            }
        }
        // Append the ul to the docDetail element
        docDetail.appendChild(ul);
    } catch (error) {
        console.error(error);
    }
}
