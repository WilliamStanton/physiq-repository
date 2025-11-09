function getCookie(name) {
    let value = `; ${document.cookie}`;
    let parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
}

function addMessage(text, sender) {
    const chatWindow = document.getElementById("chat-window");

    let bubble = document.createElement("div");
    bubble.classList.add("bubble", sender);

    // If it's an AI message, parse markdown
    if (sender === "ai") {
        bubble.innerHTML = marked.parse(text);
    } else {
        bubble.innerText = text;
    }

    chatWindow.appendChild(bubble);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById("chat-input");
    let msg = input.value.trim();
    if (!msg) return;

    addMessage(msg, "user");
    input.value = "";

    addMessage("Typing...", "ai");
    const typingBubble = document.querySelector(".bubble.ai:last-child");

    fetch("/api/chat/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: "message=" + encodeURIComponent(msg)
    })
    .then(r => r.json())
    .then(data => {
        typingBubble.remove();
        addMessage(data.response, "ai");
    })
    .catch(err => {
        console.error("Fetch error:", err);
        typingBubble.remove();
        addMessage("Error connecting to server.", "ai");
    });
}

function initChat() {
    const sendBtn = document.getElementById("send-btn");
    const input = document.getElementById("chat-input");
    const chatWindow = document.getElementById("chat-window");

    if (!sendBtn || !input || !chatWindow) return;

    // Convert any pre-rendered messages with Markdown
    const messages = document.querySelectorAll('.parsed-message');
    messages.forEach(message => {
        message.innerHTML = marked.parse(message.innerHTML);
    });

    chatWindow.scrollTop = chatWindow.scrollHeight;
    requestAnimationFrame(() => {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    });
    setTimeout(() => {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }, 200);

    // Event listeners
    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    setTimeout(() =>  document.querySelector("#chat-input").click(), 3000)
}


function initPromptBubbles() {
    const chatInput = document.getElementById('chat-input');
    const quickPromptsContainer = document.getElementById('quick-prompts');

    if (!chatInput || !quickPromptsContainer) return;

    // Use event delegation - attach ONE listener to the parent
    quickPromptsContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('prompt-bubble')) {
            const promptText = e.target.getAttribute('data-prompt');
            chatInput.value = promptText;
            chatInput.focus();

            // Visual feedback
            e.target.style.opacity = '0.5';
            setTimeout(() => {
                e.target.style.opacity = '1';
            }, 200);
        }
    });
}

// Try to initialize immediately
function tryInit() {
    initChat();
    initPromptBubbles();
}

// Initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', tryInit);

// Also try to initialize whenever the function is called (for AJAX-loaded content)
// Your dashboard.js should call this after loading the chat view
if (typeof window.initChatView === 'undefined') {
    window.initChatView = function() {
        console.log("Initializing chat view...");
        tryInit();
    };
}