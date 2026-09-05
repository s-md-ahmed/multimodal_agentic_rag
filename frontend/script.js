document.addEventListener("DOMContentLoaded", () => {
    const uploadButton = document.getElementById("start-button");
    const fileInput = document.getElementById("pdf-file-input");
    const uploadCard = document.getElementById("upload-card");
    const chatWorkspace = document.getElementById("chat-workspace");
    const sendButton = document.getElementById("send-button");
    const userInput = document.getElementById("user-input");
    const chatMessages = document.getElementById("chat-messages");
    const backButton = document.getElementById("back-to-upload-btn");
    const apiKeyInput = document.getElementById("api-key-input");

    let selectedFile = null;

    // Load saved API key if present
    const savedKey = localStorage.getItem("gemini_api_key");
    if (savedKey) {
        apiKeyInput.value = savedKey;
    }

    // Save key automatically as user types
    apiKeyInput.addEventListener("input", () => {
        const key = apiKeyInput.value.trim();
        if (key) {
            localStorage.setItem("gemini_api_key", key);
        } else {
            localStorage.removeItem("gemini_api_key");
        }
    });

    // Check session state
    const activeSessionId = sessionStorage.getItem("rag_session_id");
    const currentKey = localStorage.getItem("gemini_api_key");

    if (activeSessionId && currentKey) {
        uploadCard.style.display = "none";
        chatWorkspace.style.display = "flex";
    } else {
        sessionStorage.removeItem("rag_session_id");
        uploadCard.style.display = "flex";
        chatWorkspace.style.display = "none";
    }

    // Back to upload button logic
    if (backButton) {
        backButton.addEventListener("click", () => {
            sessionStorage.removeItem("rag_session_id");
            chatWorkspace.style.display = "none";
            uploadCard.style.display = "flex";
            chatMessages.innerHTML = "";
            selectedFile = null;
            fileInput.value = "";
            uploadButton.disabled = false;
            uploadButton.textContent = "Upload & Start Chat";
        });
    }

    function getApiKeyHeaders() {
        const key = localStorage.getItem("gemini_api_key") || apiKeyInput.value.trim();
        const headers = {};
        if (key) {
            headers["X-Gemini-API-Key"] = key;
        }
        return headers;
    }

    fileInput.addEventListener("change", (event) => {
        if (event.target.files.length > 0) {
            selectedFile = event.target.files[0];
        }
    });

    // Send request to /upload-pdf first and store returned session_id
    uploadButton.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();

        const apiKey = localStorage.getItem("gemini_api_key") || apiKeyInput.value.trim();
        if (!apiKey) {
            alert("Please enter your Gemini API Key!");
            return;
        }

        if (!selectedFile) {
            alert("Please choose a PDF file!");
            return;
        }

        uploadButton.disabled = true;
        uploadButton.textContent = "Uploading & Processing PDF...";

        const formData = new FormData();
        formData.append("file", selectedFile);

        try {
            const response = await fetch("/upload-pdf", {
                method: "POST",
                headers: getApiKeyHeaders(),
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server returned status ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            
            // Store session ID for subsequent chat queries
            sessionStorage.setItem("rag_session_id", data.session_id);

            uploadCard.style.display = "none";
            chatWorkspace.style.display = "flex";

        } catch (error) {
            console.error("DETAILED UPLOAD ERROR:", error);
            alert("FAILED: " + error.message);
            uploadButton.disabled = false;
            uploadButton.textContent = "Upload & Start Chat";
        }
    });

    sendButton.addEventListener("click", (event) => {
        event.preventDefault();
        sendUserMessage();
    });

    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            sendUserMessage();
        }
    });

    // Send session_id along with prompt to /chat-with-pdf
    async function sendUserMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        const apiKey = localStorage.getItem("gemini_api_key");
        const sessionId = sessionStorage.getItem("rag_session_id");

        if (!apiKey || !sessionId) {
            alert("Session or API key missing! Returning to upload view.");
            sessionStorage.removeItem("rag_session_id");
            chatWorkspace.style.display = "none";
            uploadCard.style.display = "flex";
            return;
        }

        appendMessage(text, "user-message");
        userInput.value = "";

        // Create container ONCE with thinking status
        const botMessageDiv = appendMessage("Thinking...", "agent-message thinking-bubble");

        try {
            const formData = new FormData();
            formData.append("prompt", text);
            formData.append("session_id", sessionId);

            const response = await fetch("/chat-with-pdf", {
                method: "POST",
                headers: getApiKeyHeaders(),
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Server error " + response.status);
            }

            const data = await response.json();
            
            // Remove thinking state class and update content in-place
            botMessageDiv.classList.remove("thinking-bubble");

            if (data && data.response) {
                botMessageDiv.innerHTML = formatMarkdown(data.response);
            } else {
                botMessageDiv.innerHTML = "<em>No response returned from model.</em>";
            }
        } catch (err) {
            console.error("Chat error:", err);
            botMessageDiv.classList.remove("thinking-bubble");
            botMessageDiv.textContent = "Error: " + err.message;
        }
    }

    // Convert Markdown tags to HTML tags
    function formatMarkdown(rawText) {
        if (!rawText) return "";
        return rawText
            .replace(/^### (.*$)/gim, '<h3 style="margin: 8px 0 4px; font-size: 1.1em; font-weight: bold;">$1</h3>')
            .replace(/^## (.*$)/gim, '<h2 style="margin: 10px 0 4px; font-size: 1.25em; font-weight: bold;">$1</h2>')
            .replace(/^# (.*$)/gim, '<h1 style="margin: 12px 0 6px; font-size: 1.4em; font-weight: bold;">$1</h1>')
            .replace(/^---$/gim, '<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.2); margin: 10px 0;">')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    function appendMessage(text, className) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", className.split(" ")[0]);
        if (className.includes("thinking-bubble")) {
            messageDiv.classList.add("thinking-bubble");
        }

        if (className.includes("thinking-bubble") || className.includes("user-message")) {
            messageDiv.textContent = text;
        } else {
            messageDiv.innerHTML = formatMarkdown(text);
        }

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    }
});
