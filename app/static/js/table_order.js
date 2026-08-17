const cart = new Map();
const cartItems = document.querySelector("#cartItems");
const cartTotal = document.querySelector("#cartTotal");
const tableOrderForm = document.querySelector("#tableOrderForm");
const tableOrderMessage = document.querySelector("#tableOrderMessage");

const moneyFormatter = new Intl.NumberFormat("zh-TW", {
  maximumFractionDigits: 0,
});

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getCartTotal() {
  return Array.from(cart.values()).reduce((total, item) => {
    if (item.is_market_price) return total;
    return total + item.unit_price * item.quantity;
  }, 0);
}

function hasMarketPriceItem() {
  return Array.from(cart.values()).some((item) => item.is_market_price);
}

function renderCart() {
  if (!cartItems || !cartTotal) return;

  if (cart.size === 0) {
    cartItems.innerHTML = '<p class="text-muted mb-0">尚未加入餐點。</p>';
    cartTotal.textContent = "NT$ 0";
    return;
  }

  cartItems.innerHTML = Array.from(cart.values()).map((item) => `
    <div class="cart-item" data-cart-id="${item.cart_id}">
      <div>
        <strong>${escapeHtml(item.specification ? `${item.item_name}（${item.specification}）` : item.item_name)}</strong>
        <span>${escapeHtml(item.display_price_label)} x ${item.quantity}</span>
        ${item.note ? `<small>備註：${escapeHtml(item.note)}</small>` : ""}
        <small>${item.is_market_price ? "小計需由店家確認" : `小計 NT$ ${moneyFormatter.format(item.unit_price * item.quantity)}`}</small>
      </div>
      <div class="cart-item__controls">
        <input class="form-control form-control-sm" type="number" min="1" value="${item.quantity}" data-cart-quantity>
        <button class="btn btn-sm btn-outline-danger" type="button" data-remove-item>刪除</button>
      </div>
    </div>
  `).join("");

  cartTotal.textContent = hasMarketPriceItem() ? "需由店家確認" : `NT$ ${moneyFormatter.format(getCartTotal())}`;
}

function buildCartId(itemElement, note) {
  const specificationSelect = itemElement.querySelector("[data-specification]");
  const specification = specificationSelect ? specificationSelect.value : "";
  return `${itemElement.dataset.id || itemElement.dataset.name}::${specification}::${note}`;
}

function addCartItemFromElement(itemElement, quantity, requestedSpecification = "", note = "") {
  const quantityInput = itemElement.querySelector("[data-quantity]");
  const specificationSelect = itemElement.querySelector("[data-specification]");
  if (specificationSelect && requestedSpecification) {
    const option = Array.from(specificationSelect.options).find(
      (candidate) => candidate.value === requestedSpecification,
    );
    if (option) {
      specificationSelect.value = requestedSpecification;
    }
  }

  const selectedOption = specificationSelect ? specificationSelect.selectedOptions[0] : null;
  const noteInput = itemElement.querySelector("[data-item-note]");
  const itemNote = note || (noteInput ? noteInput.value.trim() : "");
  const addQuantity = Math.max(Number(quantity || quantityInput?.value) || 1, 1);
  const cartId = buildCartId(itemElement, itemNote);
  const existing = cart.get(cartId);
  const isMarketPrice = itemElement.dataset.marketPrice === "1";
  const specification = selectedOption ? selectedOption.value : "";
  const unitPrice = selectedOption
    ? Number(selectedOption.dataset.price) || 0
    : Number(itemElement.dataset.price) || 0;
  const displayPriceLabel = selectedOption
    ? (selectedOption.dataset.priceLabel || `NT$ ${unitPrice}`)
    : (itemElement.dataset.displayPriceLabel || itemElement.dataset.priceLabel || "請洽店家");

  cart.set(cartId, {
    cart_id: cartId,
    menu_item_id: itemElement.dataset.id ? Number(itemElement.dataset.id) : null,
    item_name: itemElement.dataset.name,
    specification,
    unit_price: isMarketPrice ? 0 : unitPrice,
    price_label: itemElement.dataset.priceLabel || "時價",
    display_price_label: displayPriceLabel,
    is_market_price: isMarketPrice,
    image_filename: itemElement.dataset.imageFilename || null,
    note: itemNote,
    quantity: existing ? existing.quantity + addQuantity : addQuantity,
  });

  if (quantityInput) quantityInput.value = "1";
  if (noteInput && !note) noteInput.value = "";
  renderCart();
  return true;
}

document.querySelectorAll("[data-add-item]").forEach((button) => {
  button.addEventListener("click", () => {
    const itemElement = button.closest(".takeout-card");
    addCartItemFromElement(itemElement);
  });
});

window.RestaurantCart = {
  addItem(item) {
    const itemElement = document.querySelector(`.takeout-card[data-id="${item.menu_item_id}"]`);
    if (!itemElement) return false;
    return addCartItemFromElement(itemElement, item.quantity, item.specification);
  },
};

if (cartItems) {
  cartItems.addEventListener("input", (event) => {
    if (!event.target.matches("[data-cart-quantity]")) return;

    const cartItem = event.target.closest(".cart-item");
    const item = cart.get(cartItem.dataset.cartId);
    if (!item) return;

    item.quantity = Math.max(Number(event.target.value) || 1, 1);
    cart.set(item.cart_id, item);
    renderCart();
  });

  cartItems.addEventListener("click", (event) => {
    if (!event.target.matches("[data-remove-item]")) return;

    const cartItem = event.target.closest(".cart-item");
    cart.delete(cartItem.dataset.cartId);
    renderCart();
  });
}

if (tableOrderForm) {
  renderCart();

  tableOrderForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    tableOrderMessage.textContent = "";

    if (cart.size === 0) {
      tableOrderMessage.textContent = "請先加入至少一項餐點。";
      tableOrderMessage.className = "form-message text-danger";
      return;
    }

    const formData = new FormData(tableOrderForm);
    const payload = Object.fromEntries(formData.entries());
    payload.table_number = tableOrderForm.dataset.tableNumber;
    payload.total_amount = getCartTotal();
    payload.has_market_price_item = hasMarketPriceItem();
    payload.items = Array.from(cart.values()).map((item) => ({
      menu_item_id: item.menu_item_id,
      item_name: item.item_name,
      specification: item.specification,
      unit_price: item.unit_price,
      quantity: item.quantity,
      image_filename: item.image_filename,
      is_market_price: item.is_market_price,
      note: item.note,
    }));

    try {
      const response = await fetch("/orders/dine-in", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json().catch(() => ({}));

      tableOrderMessage.textContent = response.ok ? result.message : (result.error || `內用訂單送出失敗，HTTP ${response.status}`);
      tableOrderMessage.className = response.ok ? "form-message text-success" : "form-message text-danger";

      if (response.ok) {
        cart.clear();
        tableOrderForm.reset();
        renderCart();
      }
    } catch (error) {
      tableOrderMessage.textContent = `內用訂單送出失敗：${error.message}`;
      tableOrderMessage.className = "form-message text-danger";
    }
  });
}
