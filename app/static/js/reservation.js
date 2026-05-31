const reservationForm = document.querySelector("#reservationForm");
const reservationMessage = document.querySelector("#reservationMessage");

if (reservationForm) {
  reservationForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(reservationForm);

    try {
      const response = await fetch("/reservations", {
        method: "POST",
        body: formData,
      });
      const result = await response.json().catch(() => ({}));

      if (response.ok) {
        reservationMessage.textContent = result.message || "訂位已送出，店家將盡快確認。";
        reservationMessage.className = "form-message text-success";
        reservationForm.reset();
        return;
      }

      reservationMessage.textContent = result.error || `訂位送出失敗，HTTP ${response.status}`;
      reservationMessage.className = "form-message text-danger";
    } catch (error) {
      reservationMessage.textContent = `訂位送出失敗：${error.message}`;
      reservationMessage.className = "form-message text-danger";
    }
  });
}
