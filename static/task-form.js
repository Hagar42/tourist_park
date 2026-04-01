// --- Photo capture & resize ---

const MAX_WIDTH = 1200;
const JPEG_QUALITY = 0.7;

function setupPhotoCapture() {
    const input = document.getElementById("photo-input");
    const preview = document.getElementById("photo-preview");
    const hidden = document.getElementById("photo-data");
    const removeBtn = document.getElementById("photo-remove");

    if (!input) return;

    input.addEventListener("change", function () {
        const file = this.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function (e) {
            const img = new Image();
            img.onload = function () {
                // Resize via canvas
                const canvas = document.createElement("canvas");
                let w = img.width;
                let h = img.height;
                if (w > MAX_WIDTH) {
                    h = Math.round((h * MAX_WIDTH) / w);
                    w = MAX_WIDTH;
                }
                canvas.width = w;
                canvas.height = h;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(img, 0, 0, w, h);

                const dataUrl = canvas.toDataURL("image/jpeg", JPEG_QUALITY);
                hidden.value = dataUrl;
                preview.src = dataUrl;
                preview.style.display = "block";
                if (removeBtn) removeBtn.style.display = "inline-block";
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });

    if (removeBtn) {
        removeBtn.addEventListener("click", function () {
            hidden.value = "";
            preview.style.display = "none";
            removeBtn.style.display = "none";
            input.value = "";
        });
    }
}

// --- Geolocation ---

function setupGeolocation() {
    const btn = document.getElementById("geo-btn");
    const latField = document.getElementById("latitude");
    const lngField = document.getElementById("longitude");
    const status = document.getElementById("geo-status");

    if (!btn || !navigator.geolocation) {
        if (btn) btn.style.display = "none";
        return;
    }

    btn.addEventListener("click", function () {
        btn.disabled = true;
        status.textContent = "Locating...";

        navigator.geolocation.getCurrentPosition(
            function (pos) {
                latField.value = pos.coords.latitude.toFixed(6);
                lngField.value = pos.coords.longitude.toFixed(6);
                status.textContent =
                    pos.coords.latitude.toFixed(4) +
                    ", " +
                    pos.coords.longitude.toFixed(4);
                status.className = "geo-status geo-ok";
                btn.disabled = false;
            },
            function (err) {
                status.textContent = "Unable to get location: " + err.message;
                status.className = "geo-status geo-err";
                btn.disabled = false;
            },
            { enableHighAccuracy: true, timeout: 15000 }
        );
    });
}

// --- Init ---

document.addEventListener("DOMContentLoaded", function () {
    setupPhotoCapture();
    setupGeolocation();
});
