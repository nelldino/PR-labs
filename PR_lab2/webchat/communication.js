let ws;
let username = prompt("Enter your username:");
let room = "";

function joinRoom() {
    room = document.getElementById("room").value;
    ws = new WebSocket("ws://localhost:6790");  // Match server port

    ws.onopen = () => {
        ws.send(JSON.stringify({ command: "join", username, room }));
    };

    ws.onmessage = (event) => {
        const chatbox = document.getElementById("chatbox");
        const message = document.createElement("div");
        message.textContent = event.data;
        chatbox.appendChild(message);
    };

    ws.onclose = () => {
    console.log("WebSocket connection closed");
    const chatbox = document.getElementById("chatbox");
    const message = document.createElement("div");
    message.textContent = "Disconnected from the server.";
    chatbox.appendChild(message);
};
    ws.onerror = (error) => {
    console.error("WebSocket error:", error);
    const chatbox = document.getElementById("chatbox");
    const message = document.createElement("div");
    message.textContent = "Error connecting to the server.";
    chatbox.appendChild(message);
};

}

function sendMessage() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const input = document.getElementById("message");
        const message = input.value;
        ws.send(JSON.stringify({ command: "message", username, room, message }));
        input.value = "";
    } else {
        alert("You are not connected to a room.");
    }
}

function leaveRoom() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ command: "leave", username, room }));
        ws.close();
    }
}
