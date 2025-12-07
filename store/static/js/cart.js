function formatNumberWithCommas(number) {
    // Ensure the number is a string before running replace
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function approximatePrice(amount, breakpoint = 250) {
    // 1. Define the base denomination (the least exchangable bill)
    const denomination = 500;

    // 2. Calculate the remainder when dividing by the denomination
    const remainder = amount % denomination;

    let payableAmount;

    if (remainder >= breakpoint) {
        // 3. If the remainder is greater than or equal to the breakpoint (e.g., 250),
        //    we round up to the next multiple of 500.
        //    (amount - remainder) gets us the lower multiple of 500, then we add 500.
        payableAmount = amount - remainder + denomination;
    } else {
        // 4. If the remainder is less than the breakpoint,
        //    we round down to the lower multiple of 500.
        payableAmount = amount - remainder;
    }

    return payableAmount;
}

document.addEventListener('DOMContentLoaded', function () {
    const productSearchInput = document.getElementById('productSearchInput');
    const productDatalist = document.getElementById('productOptions');
    // We keep productSelect, but it's now the hidden input for the ID
    const productSelect = document.getElementById('productSelect');

    const SaleTypeSelect = document.getElementById('saleTypeSelect');
    const originalPriceSpan = document.getElementById('originalPrice');
    const sypPriceSpan = document.getElementById('sypPrice');
    const profitSelect = document.getElementById('profitSelect');
    const profitPriceSpan = document.getElementById('profitPrice');
    const sypProfitPriceSpan = document.getElementById('sypProfitPrice');
    const quantityInput = document.getElementById('quantityInput');
    const totalPriceSpan = document.getElementById('totalPrice');
    const totalSypPriceSpan = document.getElementById('totalSypPrice');
    const addToCartBtn = document.getElementById('addToCartBtn');
    const cartItems = document.getElementById('cartItems');
    const cartTotalPriceSpan = document.getElementById('cartTotalPrice');
    const sellForm = document.getElementById('sellForm');
    const cartTotalSypPriceSpan = document.getElementById('cartTotalSypPrice');
    const cartAprTotalSypPriceSpan = document.getElementById('cartAprTotalSypPrice');//hello

    const cartDataInput = document.getElementById('cartDataInput');
    const payablePriceInput = document.getElementById('payablePriceInput');//hello

    const cartTotalSypProfitSpan = document.getElementById('cartTotalSypProfit');
    const cartTotalProfitSpan = document.getElementById('cartTotalProfit');
    const productQuantity = document.getElementById('product_quantity');//tareek

    // for the option value 
    const retailPercentOption = document.getElementById('retailPercentOption');
    const wholePercentOption = document.getElementById('wholePercentOption');

    // for the option text value 
    const retailPercentText = document.getElementById('retailPercent');
    const wholePercentText = document.getElementById('wholePercent');

    const clearSearchButton = document.getElementById('clearSearch');

    let cart = [];

    // ===============================================
    // UPDATED clearForm Function
    // ===============================================
    function clearForm() {
        // 1. Reset INPUT values
        productSearchInput.value = "";    // Clear the searchable product name
        productSelect.value = 0;          // Reset the hidden product ID to 0
        quantityInput.value = 1;          // Reset quantity to 1
        SaleTypeSelect.value = "0";       // Reset sale type to default (مفرق/0)

        // 2. Reset profit select options (FIX for NaN issue)
        retailPercentText.textContent = "0 %";
        wholePercentText.textContent = "0 %";
        retailPercentOption.value = 0;
        wholePercentOption.value = 0;
        profitSelect.value = 0; // Select the '0' value option

        // 3. Recalculate all prices based on the new empty state
        // This will set all price spans to "0.00" or "0"
        calculatePrices();
    }

    // ===============================================
    // UPDATED calculatePrices Function
    // ===============================================
    function calculatePrices() {
        const saleType = SaleTypeSelect.value;
        const selectedProductName = productSearchInput.value;
        const selectedOption = productDatalist.querySelector(`option[value="${selectedProductName}"]`);

        // Default values for calculations if no product is selected or input is invalid
        let productId = 0;
        let productName = productSearchInput.placeholder;
        let originalPrice = 0;
        let sypPrice = 0;
        let availableQuantity = 0;
        let retailPercent = 0;
        let wholePercent = 0;

        if (selectedOption) {
            // Product is selected, extract data attributes
            productId = selectedOption.getAttribute('data-id');
            productName = selectedProductName;
            originalPrice = parseFloat(selectedOption.getAttribute('data-price')) || 0;
            sypPrice = parseFloat(selectedOption.getAttribute('data-syp-price')) || 0;
            availableQuantity = parseInt(selectedOption.getAttribute('data-qty')) || 0;
            retailPercent = selectedOption.getAttribute('retail-percent');
            wholePercent = selectedOption.getAttribute('whole-percent');

            productSelect.value = productId;
        } else {
            productSelect.value = 0;
        }

        const profitPercentage = parseFloat(profitSelect.value) / 100;

        // --- FIX for Quantity Typing Issue ---
        let quantity = parseInt(quantityInput.value);
        if (isNaN(quantity) || quantity < 0) {
            quantity = 0; // Treat empty/invalid/negative as 0 for calculation
            // We DO NOT reset quantityInput.value here
        }
        // --- END FIX ---

        // --- Calculation and Display ---
        productQuantity.textContent = availableQuantity;

        originalPriceSpan.textContent = originalPrice.toFixed(2);
        sypPriceSpan.textContent = formatNumberWithCommas(sypPrice.toFixed(0));

        const profitPrice = originalPrice * (1 + profitPercentage);
        const sypProfitPrice = sypPrice * (1 + profitPercentage);

        // profitPriceSpan.textContent = profitPrice.toFixed(2);
        // sypProfitPriceSpan.textContent = formatNumberWithCommas(sypProfitPrice.toFixed(0));

        profitPriceSpan.textContent = Number.isNaN(profitPrice) ? "- - -" : profitPrice.toFixed(2);
        sypProfitPriceSpan.textContent = Number.isNaN(sypProfitPrice)
            ? "- - -"
            : formatNumberWithCommas(sypProfitPrice.toFixed(0));

        const totalPrice = profitPrice * quantity;
        const totalSypPrice = sypProfitPrice * quantity;

        // totalPriceSpan.textContent = totalPrice.toFixed(2);
        // totalSypPriceSpan.textContent = formatNumberWithCommas(totalSypPrice.toFixed(0));

        totalPriceSpan.textContent = Number.isNaN(totalPrice) ? "- - -" : totalPrice.toFixed(2);
        totalSypPriceSpan.textContent = Number.isNaN(totalSypPrice)
            ? "- - -"
            : formatNumberWithCommas(totalSypPrice.toFixed(0));




        retailPercentOption.value = retailPercent;
        wholePercentOption.value = wholePercent;

        if (saleType === "0") { // Retail sale (مفرق)
            retailPercentText.textContent = retailPercent + " % " + "(النسبة المقترحة)";
            wholePercentText.textContent = wholePercent + " % ";
        } else { // Wholesale sale (جملة)
            wholePercentText.textContent = wholePercent + " % " + "(النسبة المقترحة)";
            retailPercentText.textContent = retailPercent + " % ";
        }

        return {
            productId: productId,
            productName: productName,
            quantity: quantity, // Return the 'safe' quantity (0 or positive)
            profitPercentage: profitSelect.value,
            originalPrice: originalPrice,
            sypPrice: sypPrice,
            profitPrice: profitPrice,
            sypProfitPrice: sypProfitPrice,
            totalPrice: totalPrice,
            totalSypPrice: totalSypPrice,
            availableQuantity: availableQuantity,
        };
    }

    // ===============================================
    // Cart Summary and Rendering (Logic remains the same)
    // ===============================================
    function updateCartSummary() {
        const totalPrice = cart.reduce((sum, item) => sum + item.totalPrice, 0);
        const totalSypPrice = cart.reduce((sum, item) => sum + item.totalSypPrice, 0);
        const aprtotalSypPrice = approximatePrice(totalSypPrice);//hello

        const totalProfit = cart.reduce((sum, item) => sum + item.quantity * (item.profitPrice - item.originalPrice), 0);
        const totalSypProfit = cart.reduce((sum, item) => sum + item.quantity * (item.sypProfitPrice - item.sypPrice), 0);

        cartTotalPriceSpan.textContent = totalPrice.toFixed(2);
        cartTotalSypPriceSpan.textContent = formatNumberWithCommas(totalSypPrice.toFixed(0));
        cartAprTotalSypPriceSpan.textContent = formatNumberWithCommas(aprtotalSypPrice.toFixed(0));//hello
        cartTotalProfitSpan.textContent = totalProfit.toFixed(2);
        cartTotalSypProfitSpan.textContent = formatNumberWithCommas(totalSypProfit.toFixed(0));
    }

    function renderCart() {
        cartItems.innerHTML = '';
        cart.forEach((item, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.productName}</td>
                <td>${item.quantity}</td>
                <td>${item.profitPercentage}%</td>
                <td>${item.totalPrice.toFixed(2)}</td>
                <td>${formatNumberWithCommas(item.totalSypPrice.toFixed(0))}</td>
                <td>
                    <button type="button" onclick="removeFromCart(${index})" class="btn red">حذف</button>
                </td>
            `;
            cartItems.appendChild(row);
        });
        updateCartSummary();
    }

    window.removeFromCart = function (index) {
        cart.splice(index, 1);
        renderCart();
    };

    // ===============================================
    // UPDATED addToCartBtn Event Listener
    // ===============================================
    addToCartBtn.addEventListener('click', function () {
        const productDetails = calculatePrices();
        const productId = productDetails.productId;
        const newQuantity = productDetails.quantity;
        const availableQuantity = productDetails.availableQuantity;

        if (productId == 0) {
            alert("يرجى اختيار منتج أولاً .");
            return;
        }

        // --- FIX: Add check for 0 quantity ---
        if (newQuantity <= 0) {
            alert('يرجى إدخال كمية صالحة (أكبر من 0).');
            quantityInput.value = 1; // Set it to 1
            calculatePrices(); // Update the UI to show totals for 1
            return; // Stop before adding to cart
        }
        // --- END FIX ---

        // Calculate the quantity already in the cart for this product
        const cartItem = cart.find(item => item.productId === productId);
        const quantityInCart = cartItem ? cartItem.quantity : 0;

        // Check if adding the new quantity exceeds the available stock
        if (newQuantity + quantityInCart > availableQuantity) {
            alert('لا يمكنك إضافة أكثر من الكمية المتوفرة.');
            return;
        }

        if (cartItem) {
            // Update the quantity and totals for an existing item in the cart
            cartItem.quantity += productDetails.quantity;
            cartItem.totalPrice += productDetails.totalPrice;
            cartItem.totalSypPrice += productDetails.totalSypPrice;
        } else {
            // Add a new item to the cart
            cart.push(productDetails);
        }

        // Now clear the form and render the cart
        clearForm();
        renderCart();
    });

    sellForm.addEventListener('submit', function (event) {
        event.preventDefault();
        if (cart.length === 0) {
            alert('يرجى إضافة المواد إلى الفاتورة قبل البيع.');
            return;
        }
        cartDataInput.value = JSON.stringify(cart);
        payablePriceInput.value = parseInt(cartAprTotalSypPriceSpan.textContent.replace(/,/g, ''), 10);//hello
        // payablePriceInput.value = cartAprTotalSypPriceSpan.textContent; //hello
        this.submit();
    });

    // --- Initial Event Listeners ---
    productSearchInput.addEventListener('input', calculatePrices);
    SaleTypeSelect.addEventListener('change', calculatePrices);
    profitSelect.addEventListener('change', calculatePrices);
    quantityInput.addEventListener('input', calculatePrices);
    clearSearchButton.addEventListener('click', clearForm);

    // Initial calculation on page load
    calculatePrices();
});