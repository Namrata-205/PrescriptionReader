import streamlit.components.v1 as components

def get_voice_command_component():
    """Return HTML/JS component for Web Speech API voice recognition"""
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .voice-button {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 8px;
            }
            .voice-button:hover {
                background-color: #45a049;
            }
            .voice-button.listening {
                background-color: #ff4444;
                animation: pulse 1.5s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            .command-display {
                margin-top: 10px;
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
                min-height: 30px;
            }
        </style>
    </head>
    <body>
        <button id="voiceBtn" class="voice-button" onclick="toggleVoiceRecognition()">
            🎤 Start Voice Commands
        </button>
        <div id="commandDisplay" class="command-display">
            Say: "Read next", "Repeat", or "Stop"
        </div>

        <script>
            let recognition;
            let isListening = false;

            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();
                recognition.continuous = true;
                recognition.interimResults = false;
                recognition.lang = 'en-US';

                recognition.onresult = function(event) {
                    const last = event.results.length - 1;
                    const command = event.results[last][0].transcript.toLowerCase().trim();
                    
                    document.getElementById('commandDisplay').innerText = 'You said: ' + command;
                    
                    // Send command to Streamlit
                    window.parent.postMessage({
                        type: 'voice_command',
                        command: command
                    }, '*');
                };

                recognition.onerror = function(event) {
                    console.error('Speech recognition error:', event.error);
                    document.getElementById('commandDisplay').innerText = 'Error: ' + event.error;
                };

                recognition.onend = function() {
                    if (isListening) {
                        recognition.start();
                    }
                };
            } else {
                document.getElementById('commandDisplay').innerText = 'Voice recognition not supported in this browser';
                document.getElementById('voiceBtn').disabled = true;
            }

            function toggleVoiceRecognition() {
                const btn = document.getElementById('voiceBtn');
                
                if (!isListening) {
                    recognition.start();
                    isListening = true;
                    btn.classList.add('listening');
                    btn.innerText = '🎤 Listening...';
                    document.getElementById('commandDisplay').innerText = 'Listening for commands...';
                } else {
                    recognition.stop();
                    isListening = false;
                    btn.classList.remove('listening');
                    btn.innerText = '🎤 Start Voice Commands';
                    document.getElementById('commandDisplay').innerText = 'Voice commands stopped';
                }
            }
        </script>
    </body>
    </html>
    """
    return html_code

def render_voice_component():
    """Render voice command component in Streamlit"""
    html_code = get_voice_command_component()
    components.html(html_code, height=150)

def process_voice_command(command):
    """Process recognized voice command"""
    command = command.lower().strip()
    
    # Normalize common variations
    if any(word in command for word in ['next', 'read next', 'continue']):
        return 'next'
    elif any(word in command for word in ['repeat', 'again', 'say again']):
        return 'repeat'
    elif any(word in command for word in ['stop', 'pause', 'quit', 'exit']):
        return 'stop'
    elif any(word in command for word in ['start', 'begin', 'read']):
        return 'start'
    else:
        return None