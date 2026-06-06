document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const chatWindow = document.getElementById("chatWindow");
    const textInput = document.getElementById("textInput");
    const sendBtn = document.getElementById("sendBtn");
    const micBtn = document.getElementById("micBtn");
    const audioPlayer = document.getElementById("audioPlayer");
    const avatarGlow = document.getElementById("avatarGlow");
    const statusBadge = document.getElementById("statusBadge");
    
    const threatText = document.getElementById("threatText");
    const gaugeBar = document.getElementById("gaugeBar");
    const logTerminal = document.getElementById("logTerminal");
    const clearLogsBtn = document.getElementById("clearLogsBtn");
    
    // Toggles
    const togglePrompt = document.getElementById("togglePrompt");
    const togglePII = document.getElementById("togglePII");
    const toggleCommand = document.getElementById("toggleCommand");
    const toggleTopic = document.getElementById("toggleTopic");
    const toggleOutput = document.getElementById("toggleOutput");
    
    // Quick Prompts
    const menuButtons = document.querySelectorAll(".menu-btn");
    
    // Audio Recording State
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;
    let isSleepingState = true; // Starts in Sleeping state

    // Voice Activation (SpeechRecognition) State
    let recognition = null;
    let recognitionActive = false;

    function initVoiceActivation() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("Native browser Speech Recognition not supported in this browser.");
            return;
        }

        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event) => {
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                const transcript = event.results[i][0].transcript.toLowerCase().trim();
                console.log("Voice activation heard:", transcript);
                
                // Match fuzzy wake words
                if (
                    transcript.includes("hey furina") || 
                    transcript.includes("hey farina") || 
                    transcript.includes("hello archon") || 
                    transcript.includes("wake up") ||
                    transcript.includes("hey verena") ||
                    transcript.includes("hey arena")
                ) {
                    console.log("Wake word detected by voice!");
                    stopVoiceActivation();
                    
                    // Automatically submit wake command
                    textInput.value = "hey furina";
                    handleTextSubmit();
                    break;
                }
            }
        };

        recognition.onend = () => {
            recognitionActive = false;
            // Restart after a short delay if still in sleeping state and not recording manually
            if (isSleepingState && !isRecording) {
                setTimeout(() => {
                    startVoiceActivation();
                }, 1000);
            }
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            if (event.error === 'not-allowed') {
                console.warn("Microphone access not allowed yet or blocked.");
            }
        };
    }

    function startVoiceActivation() {
        if (!recognition || recognitionActive || isRecording || !isSleepingState) return;
        try {
            recognition.start();
            recognitionActive = true;
            console.log("Voice activation listening...");
        } catch (e) {
            console.error("Error starting recognition:", e);
        }
    }

    function stopVoiceActivation() {
        if (!recognition || !recognitionActive) return;
        try {
            recognition.stop();
            recognitionActive = false;
            console.log("Voice activation stopped.");
        } catch (e) {
            console.error("Error stopping recognition:", e);
        }
    }

    // Initialize background bubbles
    createBubbles();
    
    // Set initial Sleeping state visuals
    statusBadge.textContent = "Sleeping";
    statusBadge.style.color = "#a855f7";
    avatarGlow.className = "avatar-glow-ring sleeping";
    
    // Fetch initial toggle state
    fetchToggles();
    
    // Start local SpeechRecognition wake-word engine
    initVoiceActivation();
    startVoiceActivation();

    // Bootstrap voice activation on first user interaction (browser security requirement)
    document.addEventListener("click", () => {
        if (isSleepingState && !isRecording && !recognitionActive) {
            startVoiceActivation();
        }
    }, { once: true });

    // Set up WebSockets safely
    let socket = null;
    if (typeof io !== "undefined") {
        try {
            socket = io();
            socket.on("connect", () => {
                addLogLine("SYSTEM", "CONNECTED", "Real-time security logs telemetry connected.");
            });
            socket.on("security_logs", (logs) => {
                renderLogs(logs);
            });
        } catch (e) {
            console.error("Socket.IO initialization error:", e);
            addLogLine("SYSTEM", "ERROR", "Failed to initialize WebSockets. Falling back to HTTP.");
        }
    } else {
        console.warn("Socket.IO client library not found. Real-time telemetry disabled.");
        addLogLine("SYSTEM", "WARNING", "WebSockets client not loaded. Real-time telemetry disabled.");
    }

    // Audio Player State Syncer
    audioPlayer.addEventListener("play", () => {
        avatarGlow.className = "avatar-glow-ring speaking";
        statusBadge.textContent = "Speaking";
        statusBadge.style.color = "var(--hydro-cyan)";
    });

    audioPlayer.addEventListener("ended", () => {
        if (isSleepingState) {
            avatarGlow.className = "avatar-glow-ring sleeping";
            statusBadge.textContent = "Sleeping";
            statusBadge.style.color = "#a855f7";
        } else {
            avatarGlow.className = "avatar-glow-ring";
            statusBadge.textContent = "Idle";
            statusBadge.style.color = "var(--hydro-cyan)";
        }
    });

    audioPlayer.addEventListener("error", () => {
        if (isSleepingState) {
            avatarGlow.className = "avatar-glow-ring sleeping";
            statusBadge.textContent = "Sleeping";
            statusBadge.style.color = "#a855f7";
        } else {
            avatarGlow.className = "avatar-glow-ring";
            statusBadge.textContent = "Idle";
            statusBadge.style.color = "var(--hydro-cyan)";
        }
    });

    // 1. Text Submission Handlers
    sendBtn.addEventListener("click", handleTextSubmit);
    textInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            handleTextSubmit();
        }
    });

    // 2. Quick Prompts Handlers
    menuButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const prompt = btn.getAttribute("data-prompt");
            textInput.value = prompt;
            handleTextSubmit();
        });
    });

    // 3. Clear Logs Handler
    clearLogsBtn.addEventListener("click", () => {
        logTerminal.innerHTML = '<div class="log-line system-log">[SYSTEM] Log buffer flushed. Standing by...</div>';
    });

    // 4. Toggle Change Handlers
    [togglePrompt, togglePII, toggleCommand, toggleTopic, toggleOutput].forEach(toggle => {
        toggle.addEventListener("change", updateToggles);
    });

    // 5. Mic/Voice Recording Handler
    micBtn.addEventListener("click", toggleRecording);

    // Core Interaction Functions
    
    function createBubbles() {
        const container = document.getElementById("bubbleContainer");
        if (!container) return;
        const bubbleCount = 15;
        
        for (let i = 0; i < bubbleCount; i++) {
            const bubble = document.createElement("div");
            bubble.className = "bubble";
            
            // Random styling
            const size = Math.random() * 60 + 20; // 20px - 80px
            bubble.style.width = `${size}px`;
            bubble.style.height = `${size}px`;
            bubble.style.left = `${Math.random() * 100}%`;
            bubble.style.animationDuration = `${Math.random() * 8 + 6}s`; // 6s - 14s
            bubble.style.animationDelay = `${Math.random() * 8}s`;
            
            container.appendChild(bubble);
        }
    }

    function addLogLine(type, status, details) {
        const line = document.createElement("div");
        line.className = "log-line";
        
        // Pick class
        if (status === "PASS") line.classList.add("pass-log");
        else if (status === "BLOCKED" || status === "HALTED") line.classList.add("block-log");
        else if (status === "ALERT" || status === "SANITIZED") line.classList.add("alert-log");
        else if (status === "START") line.classList.add("start-log");
        else if (status === "COMPLETE") line.classList.add("complete-log");
        else if (status === "BYPASSED_WARNING" || status === "UPDATE") line.classList.add("warning-log");
        else line.classList.add("system-log");

        const timestamp = new Date().toISOString().split("T")[1].slice(0, 8);
        line.textContent = `[${timestamp}] [${type}] ${status} : ${details}`;
        
        logTerminal.appendChild(line);
        logTerminal.scrollTop = logTerminal.scrollHeight;
    }

    function renderLogs(logs) {
        if (!logs) return;
        logs.forEach(log => {
            addLogLine(log.event_type, log.status, log.details);
        });
    }

    function updateThreatLevel(score) {
        // Score: 0 to 100
        let percent = "5%";
        let text = "LOW";
        let className = "threat-level-text low";
        avatarGlow.className = "avatar-glow-ring"; // Reset alert states

        if (score > 0 && score < 50) {
            percent = "40%";
            text = "CAUTION";
            className = "threat-level-text medium";
        } else if (score >= 50) {
            percent = "100%";
            text = "CRITICAL";
            className = "threat-level-text critical";
            avatarGlow.className = "avatar-glow-ring warning"; // Alert state
        }

        gaugeBar.style.width = percent;
        threatText.textContent = text;
        threatText.className = className;
    }

    function formatMessageText(text) {
        // Convert *action* into span with .action-text class
        return text.replace(/\*(.*?)\*/g, '<span class="action-text">*$1*</span>');
    }

    function appendMessage(sender, text, role) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${role}-message`;
        
        const senderSpan = document.createElement("span");
        senderSpan.className = "message-sender";
        senderSpan.textContent = sender;
        
        const textP = document.createElement("p");
        textP.className = "message-text";
        textP.innerHTML = formatMessageText(text);
        
        messageDiv.appendChild(senderSpan);
        messageDiv.appendChild(textP);
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function showTypingIndicator() {
        const indicatorDiv = document.createElement("div");
        indicatorDiv.className = "message assistant-message typing-indicator-container";
        indicatorDiv.id = "typingIndicator";
        
        const senderSpan = document.createElement("span");
        senderSpan.className = "message-sender";
        senderSpan.textContent = "Furina";
        
        const indicator = document.createElement("div");
        indicator.className = "typing-indicator";
        indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        
        indicatorDiv.appendChild(senderSpan);
        indicatorDiv.appendChild(indicator);
        chatWindow.appendChild(indicatorDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById("typingIndicator");
        if (indicator) {
            indicator.remove();
        }
    }

    // API Calls
    
    function fetchToggles() {
        fetch("/api/toggles")
            .then(res => res.json())
            .then(data => {
                togglePrompt.checked = data.prompt_injection;
                togglePII.checked = data.pii_redaction;
                toggleCommand.checked = data.command_whitelist;
                toggleTopic.checked = data.topic_filtering;
                toggleOutput.checked = data.output_validation;
            })
            .catch(err => console.error("Error fetching toggles:", err));
    }

    function updateToggles() {
        const config = {
            prompt_injection: togglePrompt.checked,
            pii_redaction: togglePII.checked,
            command_whitelist: toggleCommand.checked,
            topic_filtering: toggleTopic.checked,
            output_validation: toggleOutput.checked
        };

        fetch("/api/toggles", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(config)
        })
        .then(res => res.json())
        .then(data => {
            addLogLine("CONFIG", "SYNC", "Local toggles synced with server security framework.");
        })
        .catch(err => console.error("Error updating toggles:", err));
    }

    function handleTextSubmit() {
        const text = textInput.value.trim();
        if (!text) return;
        
        textInput.value = "";
        appendMessage("You", text, "user");
        showTypingIndicator();
        
        statusBadge.textContent = "Thinking...";
        statusBadge.style.color = "var(--gold-accent)";

        fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: text })
        })
        .then(res => res.json())
        .then(data => {
            removeTypingIndicator();
            appendMessage("Furina", data.text, "assistant");
            updateThreatLevel(data.risk_score);
            
            if (!socket || !socket.connected) {
                renderLogs(data.logs);
            }
            
            isSleepingState = (data.route === "sleeping");
            
            if (data.audio_path) {
                // Play synthesised audio response
                // Add unique query param to bypass cache
                audioPlayer.src = `${data.audio_path}?t=${new Date().getTime()}`;
                audioPlayer.play().catch(e => {
                    console.log("Auto-play blocked by browser. Click or interact to enable audio.");
                    if (isSleepingState) {
                        statusBadge.textContent = "Sleeping";
                        statusBadge.style.color = "#a855f7";
                        avatarGlow.className = "avatar-glow-ring sleeping";
                    } else {
                        statusBadge.textContent = "Idle";
                        statusBadge.style.color = "var(--hydro-cyan)";
                        avatarGlow.className = "avatar-glow-ring";
                    }
                });
            } else {
                if (isSleepingState) {
                    statusBadge.textContent = "Sleeping";
                    statusBadge.style.color = "#a855f7";
                    avatarGlow.className = "avatar-glow-ring sleeping";
                } else {
                    statusBadge.textContent = "Idle";
                    statusBadge.style.color = "var(--hydro-cyan)";
                    avatarGlow.className = "avatar-glow-ring";
                }
            }

            if (isSleepingState) {
                startVoiceActivation();
            } else {
                stopVoiceActivation();
            }
        })
        .catch(err => {
            removeTypingIndicator();
            appendMessage("Furina", "*sighs* The stage mechanics seem jammed for a moment, my dear guest. Let us retry!", "assistant");
            statusBadge.textContent = "Idle";
            statusBadge.style.color = "var(--hydro-cyan)";
            console.error("Chat error:", err);
        });
    }

    // Microphone / Web Audio Functions

    function toggleRecording() {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    }

    function startRecording() {
        stopVoiceActivation();
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert("Microphone recording is not supported in this browser or environment.");
            return;
        }

        audioChunks = [];
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.addEventListener("dataavailable", event => {
                    audioChunks.push(event.data);
                });

                mediaRecorder.addEventListener("stop", () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    uploadVoiceBlob(audioBlob);
                    
                    // Stop all tracks on the stream to release the mic icon
                    stream.getTracks().forEach(track => track.stop());
                });

                mediaRecorder.start();
                isRecording = true;
                micBtn.classList.add("recording");
                statusBadge.textContent = "Recording...";
                statusBadge.style.color = "var(--danger-red)";
                addLogLine("MIC_REC", "START", "Streaming microphone stream to client buffer.");
            })
            .catch(err => {
                console.error("Failed to access microphone:", err);
                addLogLine("MIC_REC", "ERROR", "Failed to access system voice microphone driver.");
            });
    }

    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            micBtn.classList.remove("recording");
            statusBadge.textContent = "Processing...";
            statusBadge.style.color = "var(--gold-accent)";
            addLogLine("MIC_REC", "STOP", "Client buffer stream finalized. Preparing upload...");
        }
    }

    function uploadVoiceBlob(blob) {
        const formData = new FormData();
        formData.append("audio", blob, "recording.webm");
        
        showTypingIndicator();

        fetch("/api/voice", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            removeTypingIndicator();
            if (data.transcribed_text) {
                appendMessage("You (Voice)", data.transcribed_text, "user");
            }
            appendMessage("Furina", data.text, "assistant");
            updateThreatLevel(data.risk_score);
            
            if (!socket || !socket.connected) {
                renderLogs(data.logs);
            }

            isSleepingState = (data.route === "sleeping");

            if (data.audio_path) {
                audioPlayer.src = `${data.audio_path}?t=${new Date().getTime()}`;
                audioPlayer.play().catch(e => {
                    console.log("Audio playback blocked.");
                    if (isSleepingState) {
                        statusBadge.textContent = "Sleeping";
                        statusBadge.style.color = "#a855f7";
                        avatarGlow.className = "avatar-glow-ring sleeping";
                    } else {
                        statusBadge.textContent = "Idle";
                        statusBadge.style.color = "var(--hydro-cyan)";
                        avatarGlow.className = "avatar-glow-ring";
                    }
                });
            } else {
                if (isSleepingState) {
                    statusBadge.textContent = "Sleeping";
                    statusBadge.style.color = "#a855f7";
                    avatarGlow.className = "avatar-glow-ring sleeping";
                } else {
                    statusBadge.textContent = "Idle";
                    statusBadge.style.color = "var(--hydro-cyan)";
                    avatarGlow.className = "avatar-glow-ring";
                }
            }

            if (isSleepingState) {
                startVoiceActivation();
            } else {
                stopVoiceActivation();
            }
        })
        .catch(err => {
            removeTypingIndicator();
            appendMessage("Furina", "*gasps* My sound devices failed to catch your voice properly. Speak once more, my audience!", "assistant");
            statusBadge.textContent = "Idle";
            statusBadge.style.color = "var(--hydro-cyan)";
            console.error("Voice processing error:", err);
        });
    }
});
