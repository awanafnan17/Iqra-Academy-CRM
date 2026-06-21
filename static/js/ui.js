// SaaS UI Global Interactions
document.addEventListener('DOMContentLoaded', function() {
    // 1. Floating Label helper for input/select elements
    const inputs = document.querySelectorAll('.form-group-floating input, .form-group-floating select, .form-group-floating textarea');

    function checkValue(el) {
        if (el.value && el.value.trim() !== '') {
            el.classList.add('has-value');
        } else {
            el.classList.remove('has-value');
        }
    }

    inputs.forEach(input => {
        // Initial check
        checkValue(input);

        // Listeners
        input.addEventListener('input', () => checkValue(input));
        input.addEventListener('change', () => checkValue(input));
        input.addEventListener('blur', () => checkValue(input));
    });

    // 2. Ripple click effect on buttons
    const rippleButtons = document.querySelectorAll('.btn-saas, .btn-primary, .menu-item');
    rippleButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Only apply if not already ripple animating
            if (this.querySelector('.btn-ripple')) return;

            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            const circle = document.createElement('span');
            circle.style.width = circle.style.height = `${size}px`;
            circle.style.left = `${x}px`;
            circle.style.top = `${y}px`;
            circle.classList.add('btn-ripple');

            // Ripple styling inline (handled safely as transient presentation)
            circle.style.position = 'absolute';
            circle.style.borderRadius = '50%';
            circle.style.transform = 'scale(0)';
            circle.style.background = 'rgba(255, 255, 255, 0.4)';
            circle.style.animation = 'ripple-effect 0.6s linear';
            circle.style.pointerEvents = 'none';

            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(circle);

            setTimeout(() => {
                circle.remove();
            }, 600);
        });
    });

    // Add ripple animation stylesheet rules dynamically
    if (!document.getElementById('dynamic-ripple-css')) {
        const style = document.createElement('style');
        style.id = 'dynamic-ripple-css';
        style.innerHTML = `
            @keyframes ripple-effect {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // CNIC input masking
    const cnicFields = document.querySelectorAll('input[name="cnic"], input[name$="-cnic"], .cnic-mask');
    cnicFields.forEach(field => {
        field.placeholder = "XXXXX-XXXXXXX-X";
        const formatCnic = (el) => {
            let val = el.value.replace(/\D/g, '');
            if (val.length > 13) {
                val = val.substring(0, 13);
            }
            let formatted = '';
            if (val.length > 0) {
                formatted += val.substring(0, Math.min(val.length, 5));
            }
            if (val.length > 5) {
                formatted += '-' + val.substring(5, Math.min(val.length, 12));
            }
            if (val.length > 12) {
                formatted += '-' + val.substring(12, 13);
            }
            el.value = formatted;
        };
        // Run on load in case value is pre-populated
        formatCnic(field);
        field.addEventListener('input', () => formatCnic(field));
    });
});
