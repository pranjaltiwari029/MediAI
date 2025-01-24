document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const loginSignup = document.getElementById('login-signup');
    const dashboard = document.getElementById('dashboard');
    const loginDiv = document.getElementById('login');
    const signupDiv = document.getElementById('signup');
    const signupLink = document.getElementById('signup-link');
    const loginLink = document.getElementById('login-link');
    const logoutBtn = document.getElementById('logout-btn');
    const uploadForm = document.getElementById('upload-form');
    const fileUpload = document.getElementById('file-upload');
    const selectedFile = document.getElementById('selected-file');

    const validateEmail = (email) => {
        const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return re.test(email);
    };

    // Login form submission
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const emailError = document.getElementById('login-email-error');

        if (!validateEmail(email)) {
            emailError.textContent = 'Please enter a valid email address';
            emailError.classList.remove('hidden');
        } else {
            emailError.classList.add('hidden');
            console.log('Login:', email, password);
            loginSignup.classList.add('hidden');
            dashboard.classList.remove('hidden');
        }
    });

    // Signup form submission
    signupForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const name = document.getElementById('signup-name').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        const emailError = document.getElementById('signup-email-error');

        if (!validateEmail(email)) {
            emailError.textContent = 'Please enter a valid email address';
            emailError.classList.remove('hidden');
        } else {
            emailError.classList.add('hidden');
            console.log('Signup:', name, email, password);
            loginSignup.classList.add('hidden');
            dashboard.classList.remove('hidden');
        }
    });

    // Switch between login and signup forms
    signupLink.addEventListener('click', (e) => {
        e.preventDefault();
        loginDiv.classList.add('hidden');
        signupDiv.classList.remove('hidden');
    });

    loginLink.addEventListener('click', (e) => {
        e.preventDefault();
        signupDiv.classList.add('hidden');
        loginDiv.classList.remove('hidden');
    });

    // Logout
    logoutBtn.addEventListener('click', () => {
        dashboard.classList.add('hidden');
        loginSignup.classList.remove('hidden');
        loginDiv.classList.remove('hidden');
        signupDiv.classList.add('hidden');
    });

    // Trigger file input click when the upload area is clicked
    const uploadArea = document.querySelector('.border-dashed');
    uploadArea.addEventListener('click', () => {
        fileUpload.click(); // This triggers the file input click
    });

    // File input change event
    fileUpload.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            selectedFile.textContent = `Selected file: ${e.target.files[0].name}`;
            selectedFile.classList.remove('hidden');
        } else {
            selectedFile.classList.add('hidden');
        }
    });

    // File upload form submission
    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const file = fileUpload.files[0];
        const diseaseType = document.getElementById('disease-type').value;

        if (file) {
            console.log('File:', file);
            console.log('Disease Type:', diseaseType);
            alert('File uploaded and analysis started. This is a placeholder for the actual implementation.');
        } else {
            alert('Please select a file before submitting.');
        }
    });
});
