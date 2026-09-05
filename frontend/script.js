document.addEventListener("DOMContentLoaded", () => {
    const uploadForm = document.getElementById("upload-form");
    const pdfFileInput = document.getElementById("pdf-file");
    const apiKeyInput = document.getElementById("api-key");
    const chatSection = document.getElementById("chat-section");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatMessages = document.getElementById("chat-messages");

    let activeSessionId = null;

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

        try {
            const res = await fetch("http://127.0.0.1:8000/upload-pdf", {
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

            appendMessage("system", `PDF uploaded successfully. ${data.message}`);
            chatSection.style.display = "block";
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const promptText = userInput.value.trim();
        const apiKey = apiKeyInput.value.trim();

        if (!promptText || !activeSessionId) return;

        appendMessage("user", promptText);
        userInput.value = "";

        const formData = new FormData();
        formData.append("prompt", promptText);
        formData.append("session_id", activeSessionId);

        try {
            const res = await fetch("http://127.0.0.1:8000/chat-with-pdf", {
                method: "POST",
                headers: { "X-Gemini-Api-Key": apiKey },
                body: formData
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Chat request failed");
            }

            const data = await res.json();
            appendMessage("assistant", data.response);
        } catch (error) {
            appendMessage("system", `Error: ${error.message}`);
        }
    });

    function appendMessage(role, text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${role}`;
        msgDiv.textContent = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
