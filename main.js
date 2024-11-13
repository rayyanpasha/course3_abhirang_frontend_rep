function loadProducts() {
    const apiUrl = 'https://sp22q143-5000.inc1.devtunnels.ms/api/products'; // Your API endpoint
    console.log("Fetching products from:", apiUrl); // Log the API URL being used
    
    fetch(apiUrl)
        .then(response => {
            console.log("Response Status:", response.status); // Log the response status
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(products => {
            console.log('Fetched Products:', products); // Log the products returned from API

            const productGrid = document.getElementById('productGrid');
            productGrid.innerHTML = ''; // Clear any existing products before adding new ones

            // Check if the products array is empty
            if (products.length === 0) {
                console.log('No products available!');
                return;
            }

            // Iterate over the products and create product cards dynamically
            products.forEach(product => {
                console.log('Product:', product); // Log each product to verify
                const productCard = document.createElement('div');
                productCard.classList.add('product-card');
                
                productCard.innerHTML = `
                    <!-- Placeholder image for all products -->
                    <img src="https://via.placeholder.com/150" alt="${product.name}" class="product-image"> 
                    <div class="product-title">${product.name}</div>
                    <div class="product-price">Rs. ${product.price} <span class="product-original-price">Rs. ${product.price * 1.25}</span></div>
                    <button class="product-wishlist" aria-label="Add to wishlist">♡</button>
                `;
                
                productGrid.appendChild(productCard);
            });
        })
        .catch(error => {
            console.error('Error fetching products:', error);
            alert('Failed to load products. Check console for details.');
        });
}

document.addEventListener('DOMContentLoaded', function() {
    loadProducts();
});
