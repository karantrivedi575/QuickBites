let cart = [];

// Function to add product to the cart
function addToCart(productName, productPrice, productId) {
    const quantityInput = document.getElementById(`quantity-${productId}`);  // Use product ID to get the correct quantity input field
    const quantity = parseInt(quantityInput.value);  // Get the quantity from the input field

    if (quantity <= 0) {
        alert("Please select a valid quantity.");
        return;
    }

    const existingProductIndex = cart.findIndex(item => item.name === productName);

    if (existingProductIndex >= 0) {
        // Update quantity if product already exists in the cart
        cart[existingProductIndex].quantity += quantity;
    } else {
        // Add new product to the cart
        cart.push({
            name: productName,
            price: productPrice,
            quantity: quantity
        });
    }

    console.log(cart);  // For debugging, to see the cart contents
    updateCartUI();  // Update the UI (if needed)
}

// Function to update the cart UI (optional, only if you want to show the cart on the same page)
function updateCartUI() {
    let cartItemsContainer = document.getElementById('cart-items');
    cartItemsContainer.innerHTML = '';  // Clear the cart display

    cart.forEach(item => {
        const cartItemElement = document.createElement('div');
        cartItemElement.innerHTML = `${item.name} - $${item.price} x ${item.quantity}`;
        cartItemsContainer.appendChild(cartItemElement);
    });
}

// Function to handle checkout
function checkout() {
    if (cart.length === 0) {
        alert('Your cart is empty!');
        return;
    }

    fetch('/checkout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(cart),
    }).then(response => {
        if (response.ok) {
            alert('Checkout successful!');
            localStorage.removeItem('cart');  // Optional: Clear local storage after checkout
            cart = [];  // Clear the cart after checkout
            updateCartUI();  // Update the cart UI to reflect an empty cart
        } else {
            alert('Checkout failed!');
        }
    }).catch(error => {
        console.error('Error during checkout:', error);
    });
}
