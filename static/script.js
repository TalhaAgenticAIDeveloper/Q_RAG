// ============================================
// RAG Chatbot Frontend JavaScript
// ============================================

const API_BASE = "http://localhost:8000";

// DOM Elements
const chatMessages = document.getElementById("chat-messages");
const questionInput = document.getElementById("question-input");
const chatForm = document.getElementById("chat-form");
const processBtn = document.getElementById("process-btn");
const uploadStatus = document.getElementById("upload-status");
const pdfInput = document.getElementById("pdf-input");
const csvInput = document.getElementById("csv-input");
const excelInput = document.getElementById("excel-input");

// Chat History State
let chatHistory = [];
let isProcessing = false;

// ============================================
// Helper Functions
// ============================================

function showStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = `status-message ${type}`;
    
    if (type !== "info") {
        setTimeout(() => {
            uploadStatus.textContent = "";
            uploadStatus.className = "status-message";
        }, 4000);
    }
}

function resetFileInputs() {
    pdfInput.value = "";
    csvInput.value = "";
    excelInput.value = "";
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeWelcomeMessage() {
    const welcomeMsg = chatMessages.querySelector(".welcome-message");
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
}

// ============================================
// Message Display Functions
// ============================================

function addUserMessage(message) {
    removeWelcomeMessage();
    
    const messageDiv = document.createElement("div");
    messageDiv.className = "message user";
    messageDiv.innerHTML = `
        <div class="message-content">${escapeHtml(message)}</div>
        <div class="message-avatar">👤</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage() {
    removeWelcomeMessage();
    
    const messageDiv = document.createElement("div");
    messageDiv.className = "message bot";
    messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content" id="streaming-content"></div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    
    return document.getElementById("streaming-content");
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// File Upload Handler
// ============================================

processBtn.addEventListener("click", async () => {
    const formData = new FormData();
    
    // Collect files
    const pdfFiles = pdfInput.files;
    const csvFiles = csvInput.files;
    const excelFiles = excelInput.files;
    
    if (!pdfFiles.length && !csvFiles.length && !excelFiles.length) {
        showStatus("Please select at least one file!", "error");
        return;
    }
    
    // Add files to FormData
    for (let file of pdfFiles) {
        formData.append("pdf_docs", file);
    }
    for (let file of csvFiles) {
        formData.append("csv_files", file);
    }
    for (let file of excelFiles) {
        formData.append("excel_files", file);
    }
    
    processBtn.disabled = true;
    showStatus("Processing files...", "info");
    
    try {
        const response = await fetch(`${API_BASE}/api/upload`, {
            method: "POST",
            body: formData,
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Upload failed");
        }
        
        const result = await response.json();
        showStatus(`✓ ${result.message} Created ${result.chunks_created} chunks!`, "success");
        resetFileInputs();
        
    } catch (error) {
        console.error("Upload error:", error);
        showStatus(`✗ Error: ${error.message}`, "error");
    } finally {
        processBtn.disabled = false;
    }
});

// ============================================
// Chat Handler with Streaming
// ============================================

chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const question = questionInput.value.trim();
    
    if (!question) {
        showStatus("Please enter a question!", "error");
        return;
    }
    
    // Add user message to chat
    addUserMessage(question);
    
    // Clear input
    questionInput.value = "";
    
    // Disable input while processing
    questionInput.disabled = true;
    chatForm.querySelector("button").disabled = true;
    isProcessing = true;
    
    try {
        // Create bot message container
        const botContentDiv = addBotMessage();
        let fullResponse = "";
        
        // Stream response
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ question }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Chat failed");
        }
        
        // Handle Server-Sent Events (SSE)
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split("\n");
            
            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.text) {
                            fullResponse += data.text;
                            botContentDiv.textContent = fullResponse;
                            scrollToBottom();
                        }
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                    } catch (e) {
                        console.error("Parse error:", e);
                    }
                }
            }
        }
        
        // Save to history
        chatHistory.push({
            role: "user",
            message: question,
        });
        chatHistory.push({
            role: "bot",
            message: fullResponse,
        });
        
    } catch (error) {
        console.error("Chat error:", error);
        
        const errorDiv = document.createElement("div");
        errorDiv.className = "message bot";
        errorDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content" style="color: #d32f2f;">
                ✗ Error: ${escapeHtml(error.message)}
            </div>
        `;
        chatMessages.appendChild(errorDiv);
        scrollToBottom();
        
    } finally {
        questionInput.disabled = false;
        chatForm.querySelector("button").disabled = false;
        isProcessing = false;
    }
});

// ============================================
// Enter key to send message
// ============================================

questionInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !isProcessing) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event("submit"));
    }
});

// ============================================
// Initialize
// ============================================

console.log("🚀 RAG Chatbot Frontend loaded");
