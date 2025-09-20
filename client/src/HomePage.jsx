import Chatbot from './Chatbot';
import './HomePage.css';

import {useState, useRef} from 'react';

const HomePage = () => {
  const chatRef = useRef(null); // ref to the chat section
  const [programs, setPrograms] = useState([{name: "program 1", description: "description 1"}, 
    {name: "program 2", description: "description 2"}, 
    {name: "program 3", description: "descitpion 3"}
  ]);

  const scrollToChat = () => {
    chatRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

    return ( 
        <div id = "homepage">
            <section id = "main">
            <h1>Name</h1>
            <h2>Catchy Slogan</h2>
            <button onClick={scrollToChat}> Start Chat</button>
            </section>
            <section id="chat" ref={chatRef}> 
            <Chatbot></Chatbot>
            <div id = "programs">
              {programs.map((element, idx) => 
              <div class="program"> 
                <h3>{element.name}</h3>
                <p>{element.description}</p>
              </div>
              
              )}
            </div>
            </section>
        </div>
    );
}

export default HomePage;