document.addEventListener('DOMContentLoaded', function() {
    function viewInvoice(invoiceId, button) {
        // Find the corresponding details div just below the clicked button
        const detailsDiv = button.nextElementSibling; // Get the next sibling div
    
        // Check if the details div is currently visible
        if (detailsDiv.style.display === 'block') {
            // If it's visible, hide it and return
            detailsDiv.style.display = 'none';
            detailsDiv.innerHTML = ''; // Clear the content when hidden
            return;
        }
    
        // If the details div is not visible, fetch the invoice details
        fetch(`/view_invoice/${invoiceId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                detailsDiv.innerHTML = "Error: " + data.error; // Display error if any
            } else {
                // Format and display invoice data
                detailsDiv.innerHTML = `
                    <h3>Invoice Details</h3>
                    <p>Invoice ID: ${data.id}</p>
                    <p>Order ID: ${data.order_id}</p>
                    <p>Customer Name: ${data.customer_name}</p>
                    <p>Total Price: Rs. ${data.total_price}</p>
                    <p>Date Issued: ${data.date_issued}</p>
                    <h4>Items:</h4>
                    <ul>
                        ${data.items.map(item => `
                            <li>
                                ${item.name} - Rs. ${item.price} x ${item.quantity} = Rs. ${item.price * item.quantity}
                            </li>
                        `).join('')}
                    </ul>
                `;
                detailsDiv.style.display = 'block'; // Show the details div
            }
        })
        .catch(error => {
            console.error('Error retrieving invoice:', error);
            detailsDiv.innerHTML = 'Failed to retrieve invoice.';
            detailsDiv.style.display = 'block'; // Show the details div
        });
    }



    // Function to fetch completed orders
    function fetchCompletedOrders() {
        fetch('/completed_orders')
            .then(response => response.json())
            .then(data => {
                const completedOrdersDiv = document.getElementById("completed-orders");

                if (!completedOrdersDiv) {
                    console.error("The 'completed-orders' element is missing from the DOM.");
                    return;
                }

                completedOrdersDiv.innerHTML = '';

                if (data.error) {
                    alert("Error: " + data.error);
                } else {
                    // Populate completed orders dynamically
                    data.orders.forEach(order => {
                        completedOrdersDiv.innerHTML += `
                            <div class="billing-item">
                                <p>Order ID: ${order.id} - Total: Rs. ${order.total_price}</p>
                                <button onclick="generateInvoice(${order.id})">Generate Invoice</button>
                            </div>
                        `;
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching completed orders:', error);
                alert('Failed to load completed orders.');
            });
    }

    // Function to generate invoice
    function generateInvoice(orderId) {
        fetch(`/generate_invoice/${orderId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                alert("Error: " + data.error);
            } else {
                alert(`Invoice for Order ID #${orderId} generated successfully!`);
    
                // Find and remove the order element from the DOM without reloading the page
                const orderElement = document.querySelector(`button[onclick="generateInvoice(${orderId})"]`).closest('.billing-item');
                if (orderElement) {
                    orderElement.remove(); // Remove the order from the "Generate New Invoice" list
                }
    
                
            }
        })
        .catch(error => {
            console.error('Error generating invoice:', error);
            alert('Failed to generate invoice.');
        });
    }
    
    
    window.viewInvoice = viewInvoice;
    window.generateInvoice = generateInvoice;

    
    fetchCompletedOrders();
});
