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

// Inject CSS globally for professional password inputs
function injectPasswordStyles() {
    if (document.getElementById('expense-password-styles')) return;
    const style = document.createElement('style');
    style.id = 'expense-password-styles';
    style.innerHTML = `
        .password-wrapper {
            position: relative;
            display: flex;
            align-items: center;
            width: 100%;
            flex: 1 1 auto;
        }
        .password-wrapper input {
            width: 100% !important;
            flex: 1 1 auto;
            box-sizing: border-box;
            padding-right: 2.5rem !important; /* Prevent text overlapping with icon */
            border-radius: 0.375rem !important; /* Smooth rounded corners */
            transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
        }
        .password-toggle-btn {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: transparent;
            border: none;
            padding: 0;
            cursor: pointer;
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6c757d;
            transition: color 0.2s ease;
        }
        .password-toggle-btn:hover {
            color: #343a40;
        }
        .password-toggle-btn:focus {
            outline: none;
        }
    `;
    document.head.appendChild(style);
}

// Add password visibility toggle buttons to password inputs
function addPasswordToggles() {
    injectPasswordStyles();
    document.querySelectorAll('input[type="password"]').forEach((input) => {
        if (input.dataset.hasToggle) return;
        input.dataset.hasToggle = '1';

        const wrapper = document.createElement('div');
        wrapper.className = 'password-wrapper';

        const parent = input.parentNode;
        parent.replaceChild(wrapper, input);
        wrapper.appendChild(input);

        // Fix alignment by moving all margins to the wrapper
        const computedStyle = window.getComputedStyle(input);
        ['marginTop', 'marginBottom', 'marginLeft', 'marginRight'].forEach(margin => {
            if (computedStyle[margin] && computedStyle[margin] !== '0px') {
                wrapper.style[margin] = computedStyle[margin];
                input.style[margin] = '0';
            }
        });
        
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'password-toggle-btn';
        btn.innerHTML = '<span class="eye">👁️</span>';
        btn.title = 'Toggle password visibility';
        
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

        wrapper.appendChild(btn);
    });
}

document.addEventListener('DOMContentLoaded', addPasswordToggles);

// Randomize button gradients on click for colorful buttons
function randomGradient() {
    const hues = [220, 180, 260, 200, 320, 15, 40];
    const h1 = hues[Math.floor(Math.random() * hues.length)];
    const h2 = hues[Math.floor(Math.random() * hues.length)];
    const h3 = hues[Math.floor(Math.random() * hues.length)];
    return `linear-gradient(90deg, hsl(${h1} 80% 55%), hsl(${h2} 70% 45%), hsl(${h3} 70% 55%))`;
}

function attachColorfulButtons() {
    document.querySelectorAll('.colorful-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const grad = randomGradient();
            btn.style.backgroundImage = grad;
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    addPasswordToggles();
    attachColorfulButtons();
});
