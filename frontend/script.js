document.addEventListener("DOMContentLoaded", () => {
    const uploadButton = document.getElementById("start-button");
    const fileInput = document.getElementById("pdf-file-input");
    const uploadCard = document.getElementById("upload-card");
    const chatWorkspace = document.getElementById("chat-workspace");
    const sendButton = document.getElementById("send-button");
    const userInput = document.getElementById("user-input");
    const chatMessages = document.getElementById("chat-messages");

    let selectedFile = null;
    // to check if a file is uploaded by checking if the target is of type file and there is more than 0 files uploaded files is the js property
    fileInput.addEventListener("change", (event) => {
        if (event.target.files.length > 0) {
            selectedFile = event.target.files[0];
            console.log("File selected:", selectedFile.name);
        }
    });

    uploadButton.addEventListener("click", async (event) => {
        // CRITICAL: Stop the page from reloading and to prevent the chatbox from disappearing
        event.preventDefault();
        event.stopPropagation();

        if (!selectedFile) {
            alert("Please choose a PDF file first!");
            return;
        }

        uploadButton.disabled = true; //disable the upload button when file is getting uploaded
        uploadButton.textContent = "Uploading...";

        const formData = new FormData();
        formData.append("prompt", "PDF uploaded. Standing by for user prompt."); // waits for the user to write the prompt acts as a temporary placeholder
        formData.append("file", selectedFile); //gets the selectedfile object
        //the temporary placeholder is there to ensure the chat window opens up properly later u again resue a similar fetchAPI to send teh actual message
        try {
            console.log("Sending fetch request to backend..."); //sending fetchapi with a post request and formdata as the body
            const response = await fetch("http://127.0.0.1:8000/chat-with-pdf", { //the response in the js file and fastapi backend name should match
                method: "POST",
                body: formData
            });

            console.log("Response status:", response.status);
            // exception handling with error code for debugging
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server returned status ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            console.log("Success data:", data);

            // Switch views cleanly without page reload
            uploadCard.style.display = "none";
            chatWorkspace.style.display = "flex";

        } catch (error) {
            console.error("DETAILED FETCH ERROR:", error);
            alert("FAILED: " + error.message);
            uploadButton.disabled = false;
            uploadButton.textContent = "Upload & Start Chat";
        }
    }); //throw block sends if code fails in try block to catch block
    //2 eventlisteners to allow flexibility of clicking sendbutton or hitting enter
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
        const text = userInput.value.trim(); //trim the extra whitespaces
        if (!text) return;

        appendMessage(text, "user-message");
        userInput.value = "";

        const thinkingId = appendMessage("Thinking...", "agent-message thinking-bubble");

        try {
            const formData = new FormData();
            formData.append("prompt", text);

            const response = await fetch("http://127.0.0.1:8000/chat-with-pdf", {
                method: "POST",
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
            appendMessage("The resource limit is exhausted.", "agent-message");
        }
    }

    function appendMessage(text, className) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", className.split(" ")[0]); //add a div when u have sent the message
        if (className.includes("thinking-bubble")) { //if data has been sent then italicise thinking bubble
            messageDiv.style.fontStyle = "italic";
            messageDiv.style.opacity = "0.7";
        }
        const cleanText = text.replace(/\*\*/g, "").replace(/\*/g, "");
        messageDiv.textContent = cleanText; // Put text inside the box
        chatMessages.appendChild(messageDiv); // Render the box on the screen
        chatMessages.scrollTop = chatMessages.scrollHeight; //make the chat window scrollable
        return messageDiv;
    }
});