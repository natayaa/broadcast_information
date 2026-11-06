(function () {
    "use strict";

    var form = document.getElementById("broadcast-form");
    if (!form) {
        return;
    }

    var api = window.appApi;
    var select = document.getElementById("document-number-select");
    var detail = document.getElementById("broadcast-detail");
    var server = document.getElementById("broadcast-server");
    var submit = document.getElementById("broadcast-submit");
    var result = document.getElementById("broadcast-result");
    var currentDocument = "";

    function setResult(message, type) {
        result.innerHTML = "";
        if (!message) {
            return;
        }
        var alert = document.createElement("div");
        alert.className = "alert alert-" + type + " py-2 mb-0";
        alert.textContent = message;
        result.appendChild(alert);
    }

    function formatDate(value) {
        if (!value) {
            return "—";
        }
        var parsed = new Date(String(value).replace(" ", "T"));
        return isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString();
    }

    function renderDetail(document_) {
        detail.innerHTML = "";
        if (!document_) {
            detail.classList.add("d-none");
            return;
        }

        var fields = [
            ["Subject", document_.document_subject || "—"],
            ["Type", document_.document_type || "—"],
            ["Model", document_.model_tv || "—"],
            ["Uploaded", formatDate(document_.datetime_upload)],
            ["Destinations", (document_.distributed_to || []).join(", ") || "—"],
            ["Last broadcast", formatDate(document_.last_broadcast_at)],
        ];

        var list = document.createElement("dl");
        fields.forEach(function (field) {
            var term = document.createElement("dt");
            term.textContent = field[0];
            var value = document.createElement("dd");
            value.textContent = field[1];
            list.appendChild(term);
            list.appendChild(value);
        });

        detail.appendChild(list);
        detail.classList.remove("d-none");
    }

    async function loadDocuments() {
        try {
            var data = await api.requestJson("/api/documents/numbers");
            select.innerHTML = "";

            if (!data.items || !data.items.length) {
                var empty = document.createElement("option");
                empty.value = "";
                empty.textContent = "No documents available";
                select.appendChild(empty);
                select.disabled = true;
                submit.disabled = true;
                return;
            }

            var placeholder = document.createElement("option");
            placeholder.value = "";
            placeholder.textContent = "Select a document";
            select.appendChild(placeholder);

            data.items.forEach(function (number) {
                var option = document.createElement("option");
                option.value = number;
                option.textContent = number;
                select.appendChild(option);
            });
        } catch (error) {
            select.innerHTML = '<option value="">Failed to load documents</option>';
            setResult(error.message, "danger");
        }
    }

    async function loadDetail(number) {
        if (!number) {
            renderDetail(null);
            return;
        }
        try {
            var document_ = await api.requestJson("/api/documents/" + encodeURIComponent(number));
            renderDetail(document_);
        } catch (error) {
            renderDetail(null);
            setResult(error.message, "danger");
        }
    }

    select.addEventListener("change", function () {
        currentDocument = select.value;
        setResult("", "info");
        loadDetail(currentDocument);
    });

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        if (!currentDocument) {
            setResult("Select a document first.", "warning");
            return;
        }

        submit.disabled = true;
        var original = submit.innerHTML;
        submit.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending…';
        setResult("", "info");

        try {
            var response = await api.requestJson("/api/broadcast", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ document_no: currentDocument, server: server.value }),
            });
            setResult(
                "Mail delivered for " + response.document_no + " to " + response.recipients +
                " recipient(s) (" + response.direct_recipients + " direct, " + response.cc_recipients + " CC).",
                "success"
            );
            await loadDetail(currentDocument);
        } catch (error) {
            setResult(error.message, "danger");
        } finally {
            submit.disabled = false;
            submit.innerHTML = original;
        }
    });

    loadDocuments();
})();
