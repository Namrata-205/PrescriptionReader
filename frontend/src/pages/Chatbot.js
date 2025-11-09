import { useState, useEffect, useRef } from "react";
import { Send, Mic, Bot, Loader } from "lucide-react";

const Chatbot = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: "assistant",
      content:
        "Hello! I'm your medicine assistant. Ask me anything about the medicines from your prescription!",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [extractedMedicines, setExtractedMedicines] = useState([]);
  const messagesEndRef = useRef(null);

  // Get medicines from localStorage (passed from Upload page)
  useEffect(() => {
    const medicines = JSON.parse(sessionStorage.getItem("extractedMedicines") || "[]");
    setExtractedMedicines(medicines);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const speakText = (text) => {
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: messages.length + 1,
      role: "user",
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: inputMessage,
          medicines: extractedMedicines,
          conversationHistory: messages,
        }),
      });

      const data = await response.json();
      if (data.success) {
        // Remove markdown asterisks and formatting
        const cleanedResponse = data.response
          .replace(/\*\*/g, "")
          .replace(/\*/g, "")
          .replace(/##/g, "")
          .replace(/#/g, "");
        
        const aiResponse = {
          id: messages.length + 2,
          role: "assistant",
          content: cleanedResponse,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiResponse]);
        speakText(data.response);
      } else {
        throw new Error(data.error || "Failed to get response");
      }
    } catch (error) {
      console.error("Error:", error);
      const errorResponse = {
        id: messages.length + 2,
        role: "assistant",
        content:
          "Sorry, I encountered an error. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceInput = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      speakText("Voice input is not supported in your browser");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInputMessage(transcript);
      setIsListening(false);
    };

    recognition.onerror = () => {
      setIsListening(false);
      speakText("Voice input failed. Please try again.");
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const styles = {
    container: {
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    },
    main: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      maxWidth: "900px",
      margin: "0 auto",
      width: "100%",
      padding: "20px",
    },
    title: {
      color: "white",
      marginBottom: "10px",
      fontSize: "28px",
      fontWeight: "bold",
    },
    subtitle: {
      color: "rgba(255,255,255,0.8)",
      marginBottom: "20px",
      fontSize: "14px",
    },
    medicinesCard: {
      background: "rgba(255,255,255,0.15)",
      border: "1px solid rgba(255,255,255,0.2)",
      borderRadius: "8px",
      padding: "15px",
      marginBottom: "20px",
      color: "white",
    },
    medicineBadges: {
      display: "flex",
      gap: "10px",
      marginTop: "10px",
      flexWrap: "wrap",
    },
    badge: {
      background: "rgba(255,255,255,0.2)",
      padding: "8px 14px",
      borderRadius: "20px",
      fontSize: "12px",
    },
    chatCard: {
      background: "white",
      borderRadius: "12px",
      boxShadow: "0 10px 40px rgba(0,0,0,0.2)",
      display: "flex",
      flexDirection: "column",
      flex: 1,
      overflow: "hidden",
    },
    chatHeader: {
      display: "flex",
      alignItems: "center",
      gap: "12px",
      padding: "20px",
      borderBottom: "1px solid #eee",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      color: "white",
      fontSize: "18px",
      fontWeight: "bold",
    },
    messagesArea: {
      flex: 1,
      overflowY: "auto",
      padding: "20px",
      display: "flex",
      flexDirection: "column",
      gap: "16px",
    },
    messageGroup: {
      display: "flex",
      gap: "12px",
    },
    messageGroupUser: {
      justifyContent: "flex-end",
    },
    message: {
      maxWidth: "70%",
      padding: "12px 16px",
      borderRadius: "8px",
      background: "#f0f0f0",
      wordWrap: "break-word",
    },
    messageUser: {
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      color: "white",
    },
    messageTime: {
      fontSize: "12px",
      color: "#999",
      marginTop: "4px",
    },
    inputArea: {
      display: "flex",
      gap: "10px",
      padding: "20px",
      borderTop: "1px solid #eee",
      background: "#fafafa",
    },
    textarea: {
      flex: 1,
      padding: "10px 12px",
      border: "1px solid #ddd",
      borderRadius: "8px",
      fontSize: "14px",
      fontFamily: "inherit",
      resize: "none",
    },
    btn: {
      padding: "10px 16px",
      border: "none",
      borderRadius: "8px",
      cursor: "pointer",
      fontSize: "14px",
      display: "flex",
      alignItems: "center",
      gap: "6px",
      fontWeight: "500",
    },
    btnVoice: {
      background: "white",
      color: "#667eea",
      border: "1px solid #ddd",
    },
    btnSend: {
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      color: "white",
    },
    btnDisabled: {
      opacity: "0.5",
      cursor: "not-allowed",
    },
  };

  return (
    <div style={styles.container}>
      <main style={styles.main}>
        <h1 style={styles.title}>Medicine Assistant</h1>
        <p style={styles.subtitle}>
          Ask questions about medicines from your prescription
        </p>

        {extractedMedicines.length > 0 && (
          <div style={styles.medicinesCard}>
            <strong>📋 Your Prescription Medicines:</strong>
            <div style={styles.medicineBadges}>
              {extractedMedicines.map((med, idx) => (
                <div key={idx} style={styles.badge}>
                  <strong>{med.medicine_name}</strong> - {med.dosage} ({med.frequency})
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={styles.chatCard}>
          <div style={styles.chatHeader}>
            <Bot size={24} />
            Medicine Assistant
          </div>

          <div style={styles.messagesArea}>
            {messages.map((message) => (
              <div
                key={message.id}
                style={{
                  ...styles.messageGroup,
                  ...(message.role === "user" ? styles.messageGroupUser : {}),
                }}
              >
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <div
                    style={{
                      ...styles.message,
                      ...(message.role === "user" ? styles.messageUser : {}),
                    }}
                  >
                    {message.content}
                  </div>
                  <div
                    style={{
                      ...styles.messageTime,
                      textAlign: message.role === "user" ? "right" : "left",
                    }}
                  >
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                    {message.role === "assistant" && (
                      <button
                        onClick={() => speakText(message.content)}
                        style={{
                          background: "none",
                          border: "none",
                          cursor: "pointer",
                          marginLeft: "8px",
                          color: "#667eea",
                        }}
                      >
                        🔊
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div style={{ ...styles.messageGroup }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#999" }}>
                  <Loader size={16} style={{ animation: "spin 1s linear infinite" }} />
                  Thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div style={styles.inputArea}>
            <textarea
              style={styles.textarea}
              placeholder="Ask about your medicines..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              disabled={isLoading}
              rows="1"
            />
            <button
              style={{
                ...styles.btn,
                ...styles.btnVoice,
                ...(isListening || isLoading ? styles.btnDisabled : {}),
              }}
              onClick={handleVoiceInput}
              disabled={isListening || isLoading}
            >
              <Mic size={18} />
            </button>
            <button
              style={{
                ...styles.btn,
                ...styles.btnSend,
                ...(!inputMessage.trim() || isLoading ? styles.btnDisabled : {}),
              }}
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Chatbot;