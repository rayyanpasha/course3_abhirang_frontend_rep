const apiUrl = 'https://sp22q143-5000.inc1.devtunnels.ms/';

function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    fetch(`${apiUrl}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    })
    .then(response => {
        if (!response.ok) throw new Error('Login failed');
        return response.json();
    })
    .then(data => {
        console.log('Login successful:', data);
        // Redirect to a dashboard or homepage after successful login
    })
    .catch(error => {
        console.error('Login error:', error);
        document.getElementById('errorMessage').style.display = 'block';
    });
}

function handleRegistration(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const phone_number = document.getElementById('phone_number').value;
    const user_type = document.getElementById('user_type').value;
    const is_verified = user_type === 'buyer' ? 0 : 1;

    fetch(`${apiUrl}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, phone_number, user_type, is_verified })
    })
    .then(response => {
        if (!response.ok) throw new Error('Registration failed');
        return response.json();
    })
    .then(data => {
        console.log('Registration successful:', data);
        window.location.href = 'login.html'; // Redirect to login page after registration
    })
    .catch(error => {
        console.error('Registration error:', error);
        document.getElementById('registerErrorMessage').style.display = 'block';
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) loginForm.addEventListener('submit', handleLogin);

    const registerForm = document.getElementById('registerForm');
    if (registerForm) registerForm.addEventListener('submit', handleRegistration);
});
