document.addEventListener('DOMContentLoaded', () => {
    // Use a small timeout to ensure all other DOM manipulations are complete
    setTimeout(initializeVoiceAssistant, 100);
});

function initializeVoiceAssistant() {
    let voiceBtn = document.getElementById('ai-voice-btn');
    let statusText = document.getElementById('ai-voice-status');
    let clearBtn = document.getElementById('ai-clear-btn');
    
    if (!voiceBtn || !statusText) {
        console.error("AI Voice elements missing from HTML. Please add them.");
        return;
    }

    // Speech Synthesis (Text-to-Speech)
    function speakText(text) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            window.speechSynthesis.speak(utterance);
        }
    }

    // Speech Recognition (Voice-to-Text)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        statusText.textContent = "Your browser does not support Speech Recognition.";
        voiceBtn.disabled = true;
        voiceBtn.style.opacity = '0.5';
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    let isRecording = false;

    voiceBtn.addEventListener('click', () => {
        if (isRecording) {
            recognition.stop();
        } else {
            try {
                recognition.start();
            } catch (err) {
                console.error("Mic start error:", err);
            }
        }
    });

    recognition.onstart = () => {
        isRecording = true;
        voiceBtn.classList.add('listening');
        statusText.textContent = "Listening... Speak your transaction or command.";
    };

    recognition.onerror = (event) => {
        isRecording = false;
        voiceBtn.classList.remove('listening');
        if (event.error === 'not-allowed') {
            statusText.textContent = "Microphone access denied.";
            speakText("Microphone permission was denied.");
        } else if (event.error === 'no-speech') {
            statusText.textContent = "No speech detected. Try again.";
        } else {
            statusText.textContent = `Error: ${event.error}`;
        }
    };

    recognition.onnomatch = () => {
        statusText.textContent = "Speech not recognized. Please try again.";
        speakText("I didn't catch that. Please try again.");
    };

    recognition.onend = () => {
        isRecording = false;
        voiceBtn.classList.remove('listening');
    };

    recognition.onresult = async (event) => {
        const transcript = event.results[0][0].transcript.toLowerCase();
        statusText.textContent = `Recognized: "${transcript}"`;

        // --- 1. Global Navigation Commands ---
        const navCommands = {
            'open dashboard': '/',
            'open transactions': '/transactions/',
            'open categories': '/categories/',
            'open reports': '/reports/',
            'export data': '/export/',
            'logout': '/logout/'
        };

        for (const [cmd, url] of Object.entries(navCommands)) {
            if (transcript.includes(cmd)) {
                speakText(`Opening ${cmd.replace('open ', '')}`);
                statusText.textContent = "Navigating...";
                setTimeout(() => { window.location.href = url; }, 1200);
                return;
            }
        }

        // --- 2. Smart Transaction Processing ---
        statusText.textContent = "Processing transaction data...";
        
        // Extract CSRF token for Django POST request
        const csrfTokenMatch = document.cookie.match(/csrftoken=([^;]+)/);
        const csrfToken = csrfTokenMatch ? csrfTokenMatch[1] : '';

        try {
            const response = await fetch(window.PROCESS_VOICE_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ text: transcript })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.status === 'success') {
                    speakText("Transaction detected.");
                    fillTransactionForm(data, event.results[0][0].transcript);
                    statusText.innerHTML = `✅ Form auto-filled successfully! <br><small class="text-muted">Extracted: ${data.amount ? '$'+data.amount : 'No amount'}, ${data.category}, ${data.transaction_type}</small>`;
                    if (clearBtn) clearBtn.style.display = 'inline-block';
                } else {
                    statusText.textContent = "Could not parse transaction details.";
                }
            }
        } catch (err) {
            console.error("AI Fetch Error:", err);
            statusText.textContent = "Server error while processing voice.";
        }
    };

    // Auto-fill form fields
    function fillTransactionForm(data, originalText) {
        // Adapt these selectors to match your exact form field 'name' attributes
        const typeField = document.querySelector('select[name="type"], select[name="transaction_type"]');
        const amountField = document.querySelector('input[name="amount"]');
        const categoryField = document.querySelector('select[name="category"]');
        const notesField = document.querySelector('textarea[name="notes"], input[name="description"]');
        const voiceTextField = document.querySelector('input[name="voice_text"], textarea[name="voice_text"]'); // Optional hidden field

        if (typeField && data.transaction_type) {
            Array.from(typeField.options).forEach(opt => {
                if (opt.text.toLowerCase().includes(data.transaction_type)) {
                    opt.selected = true;
                    typeField.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        }
        
        if (amountField && data.amount) {
            amountField.value = data.amount;
            amountField.dispatchEvent(new Event('input', { bubbles: true }));
        }

        if (categoryField && data.category) {
            Array.from(categoryField.options).forEach(opt => {
                if (opt.text.toLowerCase() === data.category.toLowerCase() || opt.value.toLowerCase() === data.category.toLowerCase()) {
                    opt.selected = true;
                    categoryField.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        }

        if (notesField) {
            notesField.value = data.notes;
            notesField.dispatchEvent(new Event('input', { bubbles: true }));
        }
        if (voiceTextField) {
            voiceTextField.value = originalText;
        }
    }

    // Handle Clear Button click
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            const typeField = document.querySelector('select[name="type"], select[name="transaction_type"]');
            const amountField = document.querySelector('input[name="amount"]');
            const categoryField = document.querySelector('select[name="category"]');
            const notesField = document.querySelector('textarea[name="notes"], input[name="description"]');
            const voiceTextField = document.querySelector('input[name="voice_text"], textarea[name="voice_text"]');

            if (typeField) {
                typeField.selectedIndex = 0;
                typeField.dispatchEvent(new Event('change', { bubbles: true }));
            }
            if (amountField) {
                amountField.value = '';
                amountField.dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (categoryField) {
                categoryField.selectedIndex = 0;
                categoryField.dispatchEvent(new Event('change', { bubbles: true }));
            }
            if (notesField) {
                notesField.value = '';
                notesField.dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (voiceTextField) voiceTextField.value = '';

            clearBtn.style.display = 'none';
            statusText.innerHTML = 'Form cleared. Ready for new voice input.';
        });
    }
});
}