/* ========================================
   AI-FARM ENHANCED JAVASCRIPT - ALL FIXES
   ======================================== */

// Flash messages auto-dismiss
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
    
    // Initialize dropdown
    initializeDropdown();
    
    // Initialize mobile menu
    initializeMobileMenu();
});

/* ========================================
   DROPDOWN FIX - REQUIREMENT #2
   ======================================== */

function initializeDropdown() {
    // Get dropdown element
    const dropdown = document.getElementById('userDropdown');
    if (!dropdown) return;
    
    // Toggle dropdown on click
    const dropbtn = document.querySelector('.dropbtn');
    if (dropbtn) {
        dropbtn.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            dropdown.classList.toggle('show');
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        if (dropdown && !event.target.closest('.dropdown')) {
            dropdown.classList.remove('show');
        }
    });
    
    // Close dropdown when clicking a link inside it
    const dropdownLinks = dropdown.querySelectorAll('a');
    dropdownLinks.forEach(link => {
        link.addEventListener('click', function() {
            dropdown.classList.remove('show');
        });
    });
}

/* ========================================
   MOBILE MENU
   ======================================== */

function initializeMobileMenu() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
        
        // Close menu when clicking a link
        const navLinks = navMenu.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
    }
}

/* ========================================
   LOADING STATES - REQUIREMENT #9
   ======================================== */

function showLoading(buttonElement, message = 'Loading...') {
    if (!buttonElement) return null;
    
    const originalHTML = buttonElement.innerHTML;
    buttonElement.dataset.originalHTML = originalHTML;
    buttonElement.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${message}`;
    buttonElement.disabled = true;
    
    return originalHTML;
}

function hideLoading(buttonElement) {
    if (!buttonElement) return;
    
    if (buttonElement.dataset.originalHTML) {
        buttonElement.innerHTML = buttonElement.dataset.originalHTML;
        buttonElement.disabled = false;
        delete buttonElement.dataset.originalHTML;
    }
}

/* ========================================
   FORM VALIDATION
   ======================================== */

function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('error');
            
            // Remove error class on input
            input.addEventListener('input', function() {
                this.classList.remove('error');
            }, { once: true });
        }
    });
    
    return isValid;
}

/* ========================================
   EXPORT FUNCTIONS - REQUIREMENT #9
   ======================================== */

function exportToPDF() {
    // Use browser print functionality
    window.print();
}

function exportToCSV(data, filename = 'export.csv') {
    // Convert data to CSV format
    let csv = '';
    
    if (Array.isArray(data) && data.length > 0) {
        // Add headers
        const headers = Object.keys(data[0]);
        csv += headers.join(',') + '\n';
        
        // Add rows
        data.forEach(row => {
            const values = headers.map(header => {
                const value = row[header] || '';
                // Escape quotes and wrap in quotes if contains comma
                return value.toString().includes(',') ? `"${value}"` : value;
            });
            csv += values.join(',') + '\n';
        });
    }
    
    // Create and download file
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
}

/* ========================================
   NOTIFICATION SYSTEM - REQUIREMENT #9
   ======================================== */

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.innerHTML = `
        ${message}
        <button onclick="this.parentElement.remove()" class="close-btn">&times;</button>
    `;
    
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

/* ========================================
   ERROR HANDLING
   ======================================== */

function handleError(error, userMessage = 'An error occurred') {
    console.error('Error:', error);
    showNotification(userMessage, 'error');
}

/* ========================================
   DEBOUNCE UTILITY
   ======================================== */

function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/* ========================================
   LOCAL STORAGE HELPERS
   ======================================== */

function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (e) {
        console.error('LocalStorage save error:', e);
        return false;
    }
}

function getFromLocalStorage(key) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    } catch (e) {
        console.error('LocalStorage get error:', e);
        return null;
    }
}

/* ========================================
   SLIDEOUT ANIMATION
   ======================================== */

const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    input.error, select.error, textarea.error {
        border-color: #EF4444 !important;
    }
`;
document.head.appendChild(style);

/* ========================================
   GLOBAL ERROR HANDLER
   ======================================== */

window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
});

/* ========================================
   SMOOTH SCROLL
   ======================================== */

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

/* ========================================
   CONFIRM DIALOGS
   ======================================== */

function confirmAction(message) {
    return confirm(message);
}

function confirmDelete(itemName) {
    return confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`);
}

/* ========================================
   READY FLAG
   ======================================== */

window.aiIFarmScriptLoaded = true;
console.log('AI-Farm Enhanced JavaScript Loaded Successfully ✓');