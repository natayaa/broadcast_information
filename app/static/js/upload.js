(function () {
    "use strict";

    var form = document.getElementById("upload-form");
    if (!form) {
        return;
    }

    var api = window.appApi;
    var submit = document.getElementById("upload-submit");
    var result = document.getElementById("upload-result");
    var originalLabel = submit.innerHTML;

    function showResult(message, type, link) {
        result.innerHTML = "";
        var alert = document.createElement("div");
        alert.className = "alert alert-" + type;
        alert.setAttribute("role", "alert");

        var text = document.createElement("span");
        text.textContent = message;
        alert.appendChild(text);

        if (link) {
            alert.appendChild(document.createTextNode(" "));
            var anchor = document.createElement("a");
            anchor.href = link;
            anchor.target = "_blank";
            anchor.rel = "noopener";
            anchor.className = "alert-link";
            anchor.textContent = "Open the document";
            alert.appendChild(anchor);
        }
        result.appendChild(alert);
    }

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        var fileInput = document.getElementById("file");
        var divisions = document.getElementById("distributed_to");
        if (!fileInput.files.length) {
            showResult("Choose a PDF file first.", "warning");
            return;
        }
        if (!divisions.selectedOptions.length) {
            showResult("Select at least one destination division.", "warning");
            return;
        }

        submit.disabled = true;
        submit.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading…';
        result.innerHTML = "";

        try {
            var response = await api.requestJson("/api/documents", {
                method: "POST",
                body: new FormData(form),
            });
            showResult(
                "Document " + response.document_no + " uploaded successfully.",
                "success",
                "/app/documents/" + encodeURIComponent(response.document_no) + "/file"
            );
            form.reset();
        } catch (error) {
            showResult(error.message, "danger");
        } finally {
            submit.disabled = false;
            submit.innerHTML = originalLabel;
        }
    });
})();
