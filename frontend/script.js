document.addEventListener("DOMContentLoaded", () => {
    const uploadCard = document.getElementById("upload-card");
    const uploadForm = document.getElementById("upload-form");
    const pdfFileInput = document.getElementById("pdf-file");
    const apiKeyInput = document.getElementById("api-key");
    const startBtn = document.getElementById("start-button");
    
    const chatWorkspace = document.getElementById("chat-workspace");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatMessages = document.getElementById("chat-messages");
    const backBtn = document.getElementById("back-to-upload-btn");

    let activeSessionId = null;

    // Dynamically choose base URL (Render hosted origin vs local dev)
    const API_BASE_URL = window.location.origin.includes("onrender.com") 
        ? window.location.origin 
        : "http://127.0.0.1:8000";

    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const apiKey = apiKeyInput.value.trim();
        const file = pdfFileInput.files[0];

        if (!apiKey || !file) {
            alert("Please provide both an API Key and a PDF file.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        startBtn.disabled = true;
        startBtn.textContent = "Processing PDF...";

        try {
            const res = await fetch(`${API_BASE_URL}/upload-pdf`, {
                method: "POST",
                headers: { "X-Gemini-Api-Key": apiKey },
                body: formData
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Upload failed");
            }

            const data = await res.json();
            activeSessionId = data.session_id;

            uploadCard.style.display = "none";
            chatWorkspace.style.display = "flex";
            chatMessages.innerHTML = "";
            appendMessage("agent-message", `PDF uploaded successfully. ${data.message}`);
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            startBtn.disabled = false;
            startBtn.textContent = "Upload & Start Chat";
        }
    });

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const promptText = userInput.value.trim();
        const apiKey = apiKeyInput.value.trim();

        if (!promptText || !activeSessionId) return;

        appendMessage("user-message", promptText);
        userInput.value = "";

        const formData = new FormData();
        formData.append("prompt", promptText);
        formData.append("session_id", activeSessionId);

        const thinkingMsg = appendMessage("agent-message thinking-bubble", "Analyzing PDF pages...");

        try {
            const res = await fetch(`${API_BASE_URL}/chat-with-pdf`, {
                method: "POST",
                headers: { "X-Gemini-Api-Key": apiKey },
                body: formData
            });

            thinkingMsg.remove();

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Chat request failed");
            }

            const data = await res.json();
            appendMessage("agent-message", data.response);
        } catch (error) {
            if (thinkingMsg) thinkingMsg.remove();
            appendMessage("agent-message", `Error: ${error.message}`);
        }
    });

    backBtn.addEventListener("click", () => {
        chatWorkspace.style.display = "none";
        uploadCard.style.display = "block";
        activeSessionId = null;
    });

    function appendMessage(className, text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${className}`;
        msgDiv.textContent = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msgDiv;
    }
});
