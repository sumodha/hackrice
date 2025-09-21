import './HomePage.css';

import {useState, useRef, useEffect} from 'react';

const HomePage = () => {
  const chatRef = useRef(null); // ref to the chat section
  const [isTyping, setIsTyping] = useState(false);
  const [programs, setPrograms] = useState([{name: "program 1", description: "description 1"}, 
    {name: "program 2", description: "description 2"}, 
    {name: "program 3", description: "descitpion 3"}, 
    {name: "program 3", description: "descitpion 3"}
  ]);
  const [showStageB, setStageB] = useState(false);
  const [showPrograms, setShowPrograms] = useState(false);
  const [eligibility, setEligibility] = useState(false);
  const programsRef = useRef(null);

  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hello! Welcome to CareNet, I can help you find programs, answer questions about eligibility, and guide you through resources. How can I help you today?" }
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
      try {
        setIsTyping(true); // start typing indicator
      const response = await fetch(`http://localhost:5000/api/stage`, {
      method: "GET",
      headers: { "Authorization": "" }, 
    });
    if (!response.ok) {
      console.log("HTTP Error! Status: " + response.status);
      return;
    }
    const data = await response.json();


    if (data.stage === "a") {
        try{
        const response = await fetch(`http://localhost:5000/api/chat/a`, {
        method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ text : input }),
        });
        if (!response.ok) {
        console.log("HTTP Error! Status: " + response.status);
        return;
        }
        const data = await response.json();

        const botMessage = { sender: "bot", text: data.text };
        setMessages((prev) => [...prev, botMessage]);

        setPrograms(data.programs);

        try {
            const response = await fetch(`http://localhost:5000/api/stage`, {
      method: "GET",
      headers: { "Authorization": "" }, 
    });
    if (!response.ok) {
      console.log("HTTP Error! Status: " + response.status);
      return;
    }
     const data = await response.json();
      if (data.stage == "b") {
          setStageB(true);
      }



        } catch (err) {
          console.log("Fetch Error" + err);
        }

      } catch (err) {
        console.log("Fetch Error" + err);
      }
    } 
    else { // data.stage = "b"
        try{
        const res = await fetch('http://localhost:5000/api/chat/b', {
        method: "POST",
        headers: {"Content-Type": "application/json"},
       body: JSON.stringify({ text : input }),
        });
        if (!response.ok) {
        console.log("HTTP Error! Status: " + response.status);
        return;
      }
      setStageB(true);
      const data = await response.json();

      const botMessage = { sender: "bot", text: data.text };
      setMessages((prev) => [...prev, botMessage]);

      setPrograms(data.programs);
      


      } catch (err) {
        console.log("Fetch Error" + err);
      }

    }
  } catch (err) {
    console.error("Error fetching external data:", err);
    return;
  } finally {
    setIsTyping(false); // end typing indicator
  }

  }

  const sendMessage = () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    sendMessageBackend(input);
    setInput("");

    
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

  const scrollToChat = () => {
    chatRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

    const clickShowPrograms = () => {
    setShowPrograms(true);
    setTimeout(() => {
    programsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 0);
  };

  const clickCheckEligibility = () => {
    if (!eligibility){
      setEligibility(true);
      const botMessage = { sender: "bot", text: "Now, I will start asking questions regard your eligibility." };
      setMessages((prev) => [...prev, botMessage]);
    }
    else{
      const botMessage = { sender: "bot", text: "I am currently asking questions regarding your eligibility. "};
      setMessages((prev) => [...prev, botMessage]);
    } 
    
  }

 


    return ( 
        <div id = "homepage">
            <section id = "main">
            <h1>CareNet</h1>
            <h2>a net of support, woven for you</h2>
            <button onClick={scrollToChat}> Start Chat</button>
            </section>
            <section id="chat" ref={chatRef}> 
            <div className="chat-container">
      <div className="chat-header">CareBot</div>

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
         {/* Typing indicator */}
  {isTyping && (
    <div className="message bot">
      <div className="avatar">🤖</div>
      <div className="bubble typing">Typing...</div>
    </div>
  )}

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
            {showStageB && <div id="buttons-container">
              <button onClick={clickShowPrograms}>Show All Programs</button> 
              <button onClick = {clickCheckEligibility}>Check Eligibility</button> 
              
              </div>}
            {showPrograms && <div id = "programs-container">
              <h1 id="programs-header" ref={programsRef}>Programs</h1>
              <div id="programs"> 
              {programs.map((element, idx) => 
              <div className="program"> 
                <h3>{element.name}</h3>
                <p>{element.description}</p>
              </div>
              
              )}
              </div>
            </div>}
            </section>
        </div>
    );
}

export default HomePage;