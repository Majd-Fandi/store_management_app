function formatNumberWithCommas(number) {
    // Ensure the number is a string before running replace
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
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
    const cartDataInput = document.getElementById('cartDataInput');
    const cartTotalSypProfitSpan = document.getElementById('cartTotalSypProfit');
    const cartTotalProfitSpan = document.getElementById('cartTotalProfit');
    const productQuantity= document.getElementById('product_quantity');//tareek

    // for the option value 
    const retailPercentOption=document.getElementById('retailPercentOption');
    const wholePercentOption=document.getElementById('wholePercentOption');

    // for the option text value 
    const retailPercentText = document.getElementById('retailPercent');
    const wholePercentText = document.getElementById('wholePercent');
    
    let cart = [];


function clearForm() {
        // 1. Reset INPUT values
        productSearchInput.value = "";     // Clear the searchable product name
        productSelect.value = 0;           // Reset the hidden product ID to 0
        quantityInput.value = 1;           // Reset quantity to 1 (or clear it, if you prefer null)
        profitSelect.value = "";          // Reset profit percentage to the default (e.g., 3)
        SaleTypeSelect.value = "0";        // Reset sale type to default (مفرق/0)

        // 2. Clear displayed price spans to 0.00 or empty
        originalPriceSpan.textContent = "0.00";
        sypPriceSpan.textContent = "0";
        profitPriceSpan.textContent = "0.00";
        sypProfitPriceSpan.textContent = "0";
        totalPriceSpan.textContent = "0.00";
        totalSypPriceSpan.textContent = "0";

    }
    
    function calculatePrices() {
        const saleType = SaleTypeSelect.value;
        //  CHANGE: Get the selected value from the search input
        const selectedProductName = productSearchInput.value;
        //  CHANGE: Find the corresponding option in the datalist
        const selectedOption = productDatalist.querySelector(`option[value="${selectedProductName}"]`);

        // Default values for calculations if no product is selected or input is invalid
        let productId = 0;
        let productName = productSearchInput.placeholder; // Use placeholder as a fallback name
        let originalPrice = 0;
        let sypPrice = 0;
        let availableQuantity = 0; // The max quantity to check against
        // tareek
        let retailPercent=0;
        let wholePercent=0;

        if (selectedOption) {
            // Product is selected, extract data attributes
            productId = selectedOption.getAttribute('data-id');
            productName = selectedProductName; // The full name from the input
            originalPrice = parseFloat(selectedOption.getAttribute('data-price')) || 0;
            sypPrice = parseFloat(selectedOption.getAttribute('data-syp-price')) || 0;
            availableQuantity = parseInt(selectedOption.getAttribute('data-qty')) || 0;
            // tareek
            retailPercent=selectedOption.getAttribute('retail-percent');
            wholePercent=selectedOption.getAttribute('whole-percent');

            //  IMPORTANT: Set the hidden input value for form submission/cart logic
            productSelect.value = productId;
        } else {
            // Product is NOT selected, clear the hidden ID
            productSelect.value = 0;
        }
        
        const profitPercentage = parseFloat(profitSelect.value) / 100;
        
        let quantity = parseInt(quantityInput.value);
        if (isNaN(quantity) || quantity <= 0) {
            quantity = 1;
            quantityInput.value = 1;
        }

        // --- Calculation and Display (Logic remains the same) ---
        productQuantity.textContent=availableQuantity;//tareek
        originalPriceSpan.textContent = originalPrice.toFixed(2);
        sypPriceSpan.textContent = formatNumberWithCommas(sypPrice.toFixed(0));

        const profitPrice = originalPrice * (1 + profitPercentage);
        const sypProfitPrice = sypPrice * (1 + profitPercentage);

        profitPriceSpan.textContent = profitPrice.toFixed(2);
        sypProfitPriceSpan.textContent = formatNumberWithCommas(sypProfitPrice.toFixed(0));

        const totalPrice = profitPrice * quantity;
        const totalSypPrice = sypProfitPrice * quantity;

        totalPriceSpan.textContent = totalPrice.toFixed(2);
        totalSypPriceSpan.textContent = formatNumberWithCommas(totalSypPrice.toFixed(0));

        // tareek 
        retailPercentOption.value=retailPercent;
        wholePercentOption.value=wholePercent;

        if (saleType === "0") { // Retail sale (مفرق)
            retailPercentText.textContent = retailPercent+" % "+"(النسبة المقترحة)";
            wholePercentText.textContent = wholePercent+" % ";
            // profitSelect.value=retailPercent
        } else { // Wholesale sale (جملة)
            wholePercentText.textContent = wholePercent+" % "+"(النسبة المقترحة)";
            retailPercentText.textContent = retailPercent+" % ";
            // profitSelect.value=wholePercent
        }


        return {
            productId: productId, // Use the extracted ID
            productName: productName, // Use the extracted name
            quantity: quantity,
            profitPercentage: profitSelect.value,
            originalPrice: originalPrice,
            sypPrice: sypPrice,
            profitPrice: profitPrice,
            sypProfitPrice: sypProfitPrice,
            totalPrice: totalPrice,
            totalSypPrice: totalSypPrice,
            availableQuantity: availableQuantity, // Return available qty for stock check
        };
    }

    // ===============================================
    // Cart Summary and Rendering (Logic remains the same)
    // ===============================================
    function updateCartSummary() {
        const totalPrice = cart.reduce((sum, item) => sum + item.totalPrice, 0);
        const totalSypPrice = cart.reduce((sum, item) => sum + item.totalSypPrice, 0);
        const totalProfit = cart.reduce((sum, item) => sum + item.quantity*(item.profitPrice-item.originalPrice), 0);
        const totalSypProfit = cart.reduce((sum, item) => sum + item.quantity*(item.sypProfitPrice-item.sypPrice), 0);

        cartTotalPriceSpan.textContent = totalPrice.toFixed(2);
        cartTotalSypPriceSpan.textContent = formatNumberWithCommas(totalSypPrice.toFixed(0));
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
    
    addToCartBtn.addEventListener('click', function () {
        //  CHANGE: We now use the return value of calculatePrices() for product details
        const productDetails = calculatePrices();
        const productId = productDetails.productId;
        const newQuantity = productDetails.quantity;
        const availableQuantity = productDetails.availableQuantity;
        clearForm();
        
        if (productId == 0) {
            alert("يرجى اختيار منتج أولاً .");
            return;
        }

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
            // Since productDetails now holds the ADDED quantity/total, we add it.
            cartItem.quantity += productDetails.quantity;
            cartItem.totalPrice += productDetails.totalPrice;
            cartItem.totalSypPrice += productDetails.totalSypPrice;
        } else {
            // Add a new item to the cart
            cart.push(productDetails);
        }
        
        renderCart();
    });
        
    sellForm.addEventListener('submit', function (event) {
        event.preventDefault();
        if (cart.length === 0) {
            alert('يرجى إضافة المواد إلى الفاتورة قبل البيع.');
            return;
        }
        cartDataInput.value = JSON.stringify(cart);
        this.submit();
    });

    productSearchInput.addEventListener('input', calculatePrices); 
    
    SaleTypeSelect.addEventListener('change', calculatePrices);
    profitSelect.addEventListener('change', calculatePrices);
    quantityInput.addEventListener('input', calculatePrices);
    calculatePrices();
});