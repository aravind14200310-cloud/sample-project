const themeToggle = document.getElementById('themeToggle');

function applyTheme(theme) {
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
        if (themeToggle) themeToggle.textContent = 'Light Mode';
    } else {
        document.body.classList.remove('dark-mode');
        if (themeToggle) themeToggle.textContent = 'Dark Mode';
    }
}

function loadTheme() {
    const savedTheme = localStorage.getItem('expenseTheme') || 'light';
    applyTheme(savedTheme);
}

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const isDark = document.body.classList.contains('dark-mode');
        const nextTheme = isDark ? 'light' : 'dark';
        applyTheme(nextTheme);
        localStorage.setItem('expenseTheme', nextTheme);
    });
}

loadTheme();

// Add password visibility toggle buttons to password inputs
function addPasswordToggles() {
    document.querySelectorAll('input[type="password"]').forEach((input) => {
        if (input.dataset.hasToggle) return;
        input.dataset.hasToggle = '1';

        const wrapper = document.createElement('div');
        wrapper.className = 'input-group';

        const parent = input.parentNode;
        parent.replaceChild(wrapper, input);
        wrapper.appendChild(input);

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-outline-secondary password-toggle-btn';
        btn.innerHTML = '<span class="eye">👁️</span>';
        btn.addEventListener('click', () => {
            if (input.type === 'password') {
                input.type = 'text';
                btn.classList.add('active');
            } else {
                input.type = 'password';
                btn.classList.remove('active');
            }
            input.focus();
        });

        const btnWrap = document.createElement('span');
        btnWrap.className = 'input-group-text';
        btnWrap.appendChild(btn);
        wrapper.appendChild(btnWrap);
    });
}

document.addEventListener('DOMContentLoaded', addPasswordToggles);
