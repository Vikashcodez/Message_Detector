// Form validation
document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Password strength indicator
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const strengthIndicator = document.getElementById('password-strength');
            if (strengthIndicator) {
                const strength = calculatePasswordStrength(this.value);
                strengthIndicator.textContent = strength.text;
                strengthIndicator.className = 'form-text ' + strength.class;
            }
        });
    }
});

function calculatePasswordStrength(password) {
    let strength = 0;
    
    // Length check
    if (password.length > 7) strength++;
    if (password.length > 11) strength++;
    
    // Character variety checks
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    // Return result
    if (strength < 2) return {text: 'Weak', class: 'text-danger'};
    if (strength < 4) return {text: 'Moderate', class: 'text-warning'};
    return {text: 'Strong', class: 'text-success'};
}