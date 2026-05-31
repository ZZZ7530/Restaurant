(function () {
    const cards = document.querySelectorAll("[data-qrcode-card]");

    function getQrImageData(card) {
        const canvas = card.querySelector("canvas");
        if (canvas) {
            return canvas.toDataURL("image/png");
        }

        const image = card.querySelector("img");
        return image ? image.src : "";
    }

    cards.forEach((card) => {
        const target = card.querySelector("[data-qrcode-target]");
        const downloadButton = card.querySelector("[data-qrcode-download]");
        const url = target.dataset.url;

        if (!window.QRCode) {
            target.textContent = "QRCode.js 載入失敗，請確認網路連線。";
            downloadButton.classList.add("disabled");
            return;
        }

        new QRCode(target, {
            text: url,
            width: 180,
            height: 180,
            colorDark: "#111827",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H,
        });

        downloadButton.addEventListener("click", (event) => {
            event.preventDefault();
            const imageData = getQrImageData(card);
            if (!imageData) {
                return;
            }

            const link = document.createElement("a");
            link.href = imageData;
            link.download = downloadButton.dataset.filename || "table-qrcode.png";
            document.body.appendChild(link);
            link.click();
            link.remove();
        });
    });
})();
