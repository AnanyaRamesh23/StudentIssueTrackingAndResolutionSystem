/**
 * Student Issue Tracking & Resolution System
 * Client-Side Utilities & Interactivity (Pure Vanilla JS)
 * Zero frameworks, full native browser compatibility
 */

document.addEventListener('DOMContentLoaded', function () {
    // -------------------------------------------------------------------------
    // 1. MODAL HANDLING & KEYBOARD ACCESSIBILITY
    // -------------------------------------------------------------------------
    window.openModal = function (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('open');
            // Auto focus first interactive element in modal
            const firstInput = modal.querySelector('input:not([type="hidden"]), select, textarea');
            if (firstInput) {
                setTimeout(function () { firstInput.focus(); }, 100);
            }
        }
    };

    window.closeModal = function (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('open');
        }
    };

    // Close modal when clicking outside on the backdrop
    document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) {
                overlay.classList.remove('open');
            }
        });
    });

    // Close any open modal on ESC key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' || e.keyCode === 27) {
            document.querySelectorAll('.modal-overlay.open').forEach(function (modal) {
                modal.classList.remove('open');
            });
        }
    });

    // -------------------------------------------------------------------------
    // 2. SUBMIT ISSUE: DYNAMIC CATEGORY SLA & DUE DATE CALCULATION
    // -------------------------------------------------------------------------
    const categorySelect = document.getElementById('category_id');
    const slaNoticeBox = document.getElementById('sla_notice_box');
    const slaDaysText = document.getElementById('sla_days_text');
    const slaDueDateText = document.getElementById('sla_due_date_text');

    if (categorySelect && slaNoticeBox) {
        function updateSLA() {
            const selectedOption = categorySelect.options[categorySelect.selectedIndex];
            if (!selectedOption || !selectedOption.value) {
                slaNoticeBox.style.display = 'none';
                return;
            }

            const slaDays = selectedOption.getAttribute('data-sla');
            if (slaDays) {
                const days = parseInt(slaDays, 10);
                const targetDate = new Date();
                targetDate.setDate(targetDate.getDate() + days);

                if (slaDaysText) {
                    slaDaysText.textContent = days + (days === 1 ? ' business day' : ' business days');
                }
                if (slaDueDateText) {
                    slaDueDateText.textContent = targetDate.toLocaleDateString(undefined, {
                        weekday: 'short',
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                    });
                }
                slaNoticeBox.style.display = 'block';
            } else {
                slaNoticeBox.style.display = 'none';
            }
        }
        categorySelect.addEventListener('change', updateSLA);
        if (categorySelect.value) {
            updateSLA();
        }
    }

    // -------------------------------------------------------------------------
    // 3. AUTO-DISMISS FLASH NOTIFICATIONS WITH SMOOTH TRANSITION
    // -------------------------------------------------------------------------
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages.length > 0) {
        setTimeout(function () {
            flashMessages.forEach(function (msg) {
                msg.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                msg.style.opacity = '0';
                msg.style.transform = 'translateY(-10px)';
                setTimeout(function () { msg.remove(); }, 500);
            });
        }, 5000);
    }

    // -------------------------------------------------------------------------
    // 4. PREVENT ACCIDENTAL DOUBLE-SUBMISSION OF ISSUES
    // -------------------------------------------------------------------------
    const issueForms = document.querySelectorAll('form[action*="submit"]');
    issueForms.forEach(function (form) {
        form.addEventListener('submit', function () {
            const btn = form.querySelector('button[type="submit"]');
            if (btn && !btn.disabled) {
                setTimeout(function () {
                    btn.disabled = true;
                    btn.textContent = 'Submitting...';
                }, 10);
            }
        });
    });
});
