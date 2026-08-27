document.addEventListener("DOMContentLoaded", () => {
    const uploadButton = document.getElementById("start-button");
    const fileInput = document.getElementById("pdf-file-input");
    const uploadCard = document.getElementById("upload-card");
    const chatWorkspace = document.getElementById("chat-workspace");
    const sendButton = document.getElementById("send-button");
    const userInput = document.getElementById("user-input");
    const chatMessages = document.getElementById("chat-messages");
    const backButton = document.getElementById("back-to-upload-btn");
    
    // API Key Elements
    const apiKeyInput = document.getElementById("api-key-input");

    let selectedFile = null;

    // Load saved API key if present
    const savedKey = localStorage.getItem("gemini_api_key");
    if (savedKey) {
        apiKeyInput.value = savedKey;
    }

    // Check if we have an active chat session saved in browser session storage
    const activeSession = sessionStorage.getItem("rag_active_session");
    if (activeSession) {
        uploadCard.style.display = "none";
        chatWorkspace.style.display = "flex";
    } else {
        uploadCard.style.display = "flex";
        chatWorkspace.style.display = "none";
    }

    // Back to upload button logic
    if (backButton) {
        backButton.addEventListener("click", () => {
            sessionStorage.removeItem("rag_active_session");
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
        const key = apiKeyInput.value.trim();
        const headers = {};
        if (key) {
            headers["X-Gemini-API-Key"] = key;
        }
        return headers;
    }
    
    fileInput.addEventListener("change", (event) => {
        if (event.target.files.length > 0) {
            selectedFile = event.target.files[0];
            console.log("File selected:", selectedFile.name);
        }
    });

    uploadButton.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();

        const apiKey = apiKeyInput.value.trim();
        if (!apiKey) {
            alert("Please enter your Gemini API Key first!");
            return;
        }

        // Save key automatically on upload click
        localStorage.setItem("gemini_api_key", apiKey);

        if (!selectedFile) {
            alert("Please choose a PDF file first!");
            return;
        }

        uploadButton.disabled = true;
        uploadButton.textContent = "Uploading...";

        const formData = new FormData();
        formData.append("prompt", "PDF uploaded. Standing by for user prompt.");
        formData.append("file", selectedFile);
        
        try {
            console.log("Sending fetch request to backend...");
            const response = await fetch("/chat-with-pdf", {
                method: "POST",
                headers: getApiKeyHeaders(),
                body: formData
            });

            console.log("Response status:", response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server returned status ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            console.log("Success data:", data);

            // Save session state so refresh keeps them in the chat view
            sessionStorage.setItem("rag_active_session", "true");

            uploadCard.style.display = "none";
            chatWorkspace.style.display = "flex";

        } catch (error) {
            console.error("DETAILED FETCH ERROR:", error);
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

    async function sendUserMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        const apiKey = apiKeyInput.value.trim();
        if (!apiKey) {
            alert("API Key missing! Please enter your Gemini API Key.");
            return;
        }

        appendMessage(text, "user-message");
        userInput.value = "";

        const thinkingId = appendMessage("Thinking...", "agent-message thinking-bubble");

        try {
            const formData = new FormData();
            formData.append("prompt", text);

            const response = await fetch("/chat-with-pdf", {
                method: "POST",
                headers: getApiKeyHeaders(),
                body: formData
            });

            if (!response.ok) throw new Error("Server error " + response.status);

            const data = await response.json();
            thinkingId.remove();
            if (data && data.response) {
                appendMessage(data.response, "agent-message");
            }
        } catch (err) {
            console.error("Chat error:", err);
            thinkingId.remove();
            appendMessage("The resource limit is exhausted or invalid API key provided.", "agent-message");
        }
    }

    function appendMessage(text, className) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", className.split(" ")[0]); 
        if (className.includes("thinking-bubble")) { 
            messageDiv.style.fontStyle = "italic";
            messageDiv.style.opacity = "0.7";
        }
        const cleanText = text.replace(/\*\*/g, "").replace(/\*/g, "");
        messageDiv.textContent = cleanText; 
        chatMessages.appendChild(messageDiv); 
        chatMessages.scrollTop = chatMessages.scrollHeight; 
        return messageDiv;
    }
});
