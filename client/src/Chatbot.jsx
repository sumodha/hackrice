import { useState, useRef, useEffect } from "react";
import "./Chatbot.css";

const Chatbot = () => {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hi 👋 Welcome! How can I help you today?" }
  ]);
  const [input, setInput] = useState("");

  const chatBodyRef = useRef(null); // scroll only inside chat container

  // Auto scroll inside chat-body when new messages arrive
  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessageBackend = async (input) => {
    try{
      const res = await fetch('http://localhost:5000/api/chat', {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ text : input }),
      });
      if (!response.ok) {
      console.log("HTTP Error! Status: " + response.status);
    }
    } catch (err) {
      console.log("Fetch Error" + err);
    }

  }

  const sendMessage = () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    sendMessageBackend(input);
    setInput("");

    // Fake bot reply
    setTimeout(() => {
      const botMessage = { sender: "bot", text: "You said: " + input };
      setMessages((prev) => [...prev, botMessage]);
    }, 600);
  };

  

  const handleOptionClick = (option) => {
    const userMessage = { sender: "user", text: option };
    setMessages((prev) => [...prev, userMessage]);

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: `You selected: ${option}` }
      ]);
    }, 600);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">Talk to []</div>

      <div className="chat-body" ref={chatBodyRef}>
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.sender}`}>
            <div className="avatar">{msg.sender === "user" ? "👩‍🦰" : "🤖"}</div>
            <div className="bubble">{msg.text}</div>
            {msg.options && (
              <div className="options">
                {msg.options.map((opt, i) => (
                  <button key={i} onClick={() => handleOptionClick(opt)}>
                    {opt}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button onClick={sendMessage}>↑</button>
      </div>
    </div>
  );
};

export default Chatbot;
