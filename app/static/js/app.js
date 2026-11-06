(function () {
    "use strict";

    function formatDetail(detail) {
        if (Array.isArray(detail)) {
            return detail
                .map(function (item) {
                    var location = Array.isArray(item.loc) ? item.loc.join(".") + ": " : "";
                    return location + (item.msg || "Invalid value");
                })
                .join("; ");
        }
        if (detail && typeof detail === "object") {
            return detail.message || JSON.stringify(detail);
        }
        return detail || "Request failed";
    }

    async function requestJson(url, options) {
        var config = options || {};
        var headers = Object.assign({ Accept: "application/json" }, config.headers || {});
        var response = await fetch(url, Object.assign({}, config, { headers: headers }));

        var text = await response.text();
        var body = null;
        if (text) {
            try {
                body = JSON.parse(text);
            } catch (error) {
                body = text;
            }
        }

        if (!response.ok) {
            var message = body && (body.detail || body.message)
                ? formatDetail(body.detail || body.message)
                : "Request failed (" + response.status + ")";
            var failure = new Error(message);
            failure.status = response.status;
            throw failure;
        }
        return body;
    }

    function showAlert(message, type) {
        var container = document.querySelector(".app-main .container") || document.body;
        var alert = document.createElement("div");
        alert.className = "alert alert-" + (type || "success") + " alert-dismissible fade show";
        alert.setAttribute("role", "alert");

        var text = document.createElement("span");
        text.textContent = message;
        alert.appendChild(text);

        var close = document.createElement("button");
        close.type = "button";
        close.className = "btn-close";
        close.setAttribute("data-bs-dismiss", "alert");
        close.setAttribute("aria-label", "Close");
        alert.appendChild(close);

        container.prepend(alert);
        window.setTimeout(function () {
            if (window.bootstrap && window.bootstrap.Alert) {
                window.bootstrap.Alert.getOrCreateInstance(alert).close();
            }
        }, 6000);
        return alert;
    }

    document.addEventListener("click", async function (event) {
        var button = event.target.closest("[data-delete-url]");
        if (!button) {
            return;
        }
        if (!window.confirm(button.dataset.confirm || "Delete this item?")) {
            return;
        }

        button.disabled = true;
        try {
            await requestJson(button.dataset.deleteUrl, { method: "DELETE" });
            var row = button.closest("tr");
            if (row) {
                row.remove();
            }
            showAlert("Item deleted", "success");
        } catch (error) {
            button.disabled = false;
            showAlert(error.message, "danger");
        }
    });

    window.appApi = {
        requestJson: requestJson,
        formatDetail: formatDetail,
        showAlert: showAlert,
    };
})();
