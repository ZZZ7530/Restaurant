(function () {
  const assistant = document.querySelector("[data-ai-assistant]");
  if (!assistant) return;

  const mode = assistant.dataset.aiMode || "menu";
  const panel = assistant.querySelector(".ai-assistant__panel");
  const openButton = assistant.querySelector("[data-ai-open]");
  const closeButtons = assistant.querySelectorAll("[data-ai-close]");
  const form = assistant.querySelector("[data-ai-form]");
  const submitButton = assistant.querySelector("[data-ai-submit]");
  const messageBox = assistant.querySelector("[data-ai-message]");
  const resultsBox = assistant.querySelector("[data-ai-results]");

  const moneyFormatter = new Intl.NumberFormat("zh-TW", {
    maximumFractionDigits: 0,
  });

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function splitList(value) {
    return String(value || "")
      .split(/[、,，\s]+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function showMessage(text, type) {
    messageBox.textContent = text || "";
    messageBox.className = `ai-assistant__message ${type ? `is-${type}` : ""}`;
  }

  function openPanel() {
    assistant.classList.add("is-open");
    panel.setAttribute("aria-hidden", "false");
  }

  function closePanel() {
    assistant.classList.remove("is-open");
    panel.setAttribute("aria-hidden", "true");
  }

  function findMenuCard(menuItemId) {
    return document.querySelector(`[data-menu-item-id="${menuItemId}"], [data-id="${menuItemId}"]`);
  }

  function viewMenuItem(menuItemId) {
    const card = findMenuCard(menuItemId);
    if (!card) return;
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    card.classList.add("ai-highlight");
    window.setTimeout(() => card.classList.remove("ai-highlight"), 1800);
  }

  function addRecommendationItem(item) {
    if (!window.RestaurantCart || typeof window.RestaurantCart.addItem !== "function") {
      return false;
    }
    return window.RestaurantCart.addItem(item);
  }

  function imageMarkup(item) {
    if (!item.image_filename) return "";
    const imageUrl = `/static/images/background/${encodeURIComponent(item.image_filename)}`;
    return `<img class="ai-assistant__item-image" src="${imageUrl}" alt="${escapeHtml(item.name)}">`;
  }

  function actionButtons(item) {
    if (mode === "menu") {
      return `<button class="btn btn-sm btn-outline-primary" type="button" data-ai-view="${item.menu_item_id}">查看餐點</button>`;
    }
    return `<button class="btn btn-sm btn-primary" type="button" data-ai-add="${item.menu_item_id}">加入訂單</button>`;
  }

  function renderResults(data) {
    const items = data.items || [];
    window.currentAiRecommendationItems = items;
    if (!items.length) {
      resultsBox.innerHTML = '<div class="ai-assistant__empty">目前沒有可加入的推薦餐點。</div>';
      return;
    }

    const allButton = mode === "menu"
      ? ""
      : '<button class="btn btn-outline-primary w-100 mb-3" type="button" data-ai-add-all>全部加入訂單</button>';
    const warningHtml = (data.warnings || []).map((warning) => (
      `<p class="ai-assistant__warning">${escapeHtml(warning)}</p>`
    )).join("");

    resultsBox.innerHTML = `
      <div class="ai-assistant__summary">
        <strong>${escapeHtml(data.summary || "AI 為你推薦")}</strong>
        <span>固定價格合計：NT$ ${moneyFormatter.format(data.fixed_total || 0)}</span>
        ${warningHtml}
        <p>${escapeHtml(data.reason || "")}</p>
      </div>
      ${allButton}
      <button class="btn btn-outline-secondary w-100" type="button" data-ai-retry>重新推薦</button>
      <div class="ai-assistant__items">
        ${items.map((item) => `
          <article class="ai-assistant__item" data-ai-result-id="${item.menu_item_id}">
            ${imageMarkup(item)}
            <div>
              <h3>${escapeHtml(item.specification ? `${item.name}（${item.specification}）` : item.name)}</h3>
              <p>${escapeHtml(item.reason || "")}</p>
              <span>${escapeHtml(item.display_price_label)}｜數量 ${item.quantity}</span>
            </div>
            ${actionButtons(item)}
          </article>
        `).join("")}
      </div>
    `;
  }

  openButton?.addEventListener("click", openPanel);
  closeButtons.forEach((button) => button.addEventListener("click", closePanel));

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage("", "");
    resultsBox.innerHTML = "";
    submitButton.disabled = true;
    submitButton.textContent = "推薦中...";
    submitButton.classList.add("is-loading");

    const formData = new FormData(form);
    const payload = {
      mode,
      party_size: Number(formData.get("party_size")),
      budget: Number(formData.get("budget") || 0),
      preferences: splitList(formData.get("preferences")),
      dietary_needs: splitList(formData.get("dietary_needs")),
      message: formData.get("message") || "",
    };

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 15000);

    try {
      const response = await fetch("/api/ai/recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok || result.ok === false) {
        showMessage(result.message || `AI 推薦暫時不可用，HTTP ${response.status}`, "error");
        return;
      }
      renderResults(result);
      showMessage("推薦已產生，請自行確認餐點後再送出訂單。", "success");
    } catch (error) {
      const message = error.name === "AbortError" ? "AI 推薦逾時，請稍後再試。" : `AI 推薦暫時不可用：${error.message}`;
      showMessage(message, "error");
    } finally {
      window.clearTimeout(timeoutId);
      submitButton.disabled = false;
      submitButton.textContent = "幫我推薦";
      submitButton.classList.remove("is-loading");
    }
  });

  resultsBox?.addEventListener("click", (event) => {
    if (event.target.closest("[data-ai-retry]")) {
      form?.requestSubmit();
      return;
    }

    const viewButton = event.target.closest("[data-ai-view]");
    if (viewButton) {
      viewMenuItem(viewButton.dataset.aiView);
      if (window.matchMedia("(max-width: 768px)").matches) {
        closePanel();
      }
      return;
    }

    const addButton = event.target.closest("[data-ai-add]");
    if (addButton) {
      const item = getResultItem(addButton.dataset.aiAdd);
      if (item && addRecommendationItem(item)) {
        showMessage("已加入目前點餐內容，請確認數量後自行送出。", "success");
      } else {
        showMessage("找不到對應餐點，無法加入。", "error");
      }
      return;
    }

    if (event.target.closest("[data-ai-add-all]")) {
      const addedCount = (window.currentAiRecommendationItems || []).reduce((count, item) => (
        addRecommendationItem(item) ? count + 1 : count
      ), 0);
      showMessage(`已加入 ${addedCount} 道推薦餐點，請確認後自行送出。`, addedCount ? "success" : "error");
    }
  });

  function getResultItem(menuItemId) {
    return (window.currentAiRecommendationItems || []).find(
      (item) => String(item.menu_item_id) === String(menuItemId),
    );
  }
})();
