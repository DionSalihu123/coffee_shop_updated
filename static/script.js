function toggleChatbot() {
	const chatbot = document.getElementById("chatbot-container");
	chatbot.style.display = chatbot.style.display === "none" ? "flex" : "none";
}

document.getElementById("chatbot-form").addEventListener("submit", async function (e) {
	e.preventDefault();

	const input = document.getElementById("chatbot-input");
	const message = input.value.trim();
	if (!message) return;

	// Display user message
	const messages = document.getElementById("chatbot-messages");
	messages.innerHTML += `<div><strong>You:</strong> ${message}</div>`;
	input.value = "";

	// Fetch chatbot response from server
	const response = await fetch("/chatbot", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ message }),
	});

	const data = await response.json();
	messages.innerHTML += `<div><strong>Bot:</strong> ${data.response}</div>`;
	messages.scrollTop = messages.scrollHeight; // Scroll to the bottom
});
