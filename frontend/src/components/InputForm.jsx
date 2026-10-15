import React, { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./InputForm.css";

function InputForm({ onStudyGuideGenerated, user, selectedStudyGuide, setSelectedStudyGuide, isSidebarOpen, setIsSidebarOpen }) {
  const [topic, setTopic] = useState("");
  const [followUp, setFollowUp] = useState(""); // New state for follow-ups
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversation, setConversation] = useState([]); // Store full conversation
  const [displayedText, setDisplayedText] = useState("");
  const [isHovered, setIsHovered] = useState(false); // Track hover state
  // Load selected study guide's conversation history
  useEffect(() => {
    if (selectedStudyGuide) {
      setConversation(selectedStudyGuide.conversation || []);
    } else {
      setConversation([]); // Reset if no guide is selected
    }
  }, [selectedStudyGuide]);
  
  
  const startTypingEffect = (fullText) => {
    if (!fullText || typeof fullText !== "string") {
      console.warn("Typing effect received an invalid response:", fullText);
      return;
    }

    setDisplayedText(""); // Reset text before typing starts
    let index = 0;

    const interval = setInterval(() => {
      if (index < fullText.length) {
        setDisplayedText((prev) => prev + fullText[index]); 
        index++;
      } else {
        clearInterval(interval);
      }
    }, 10); // Adjust speed here

    return () => clearInterval(interval);
  };
  // Function to generate a new study guide
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    
    try {
      const response = await fetch("http://localhost:8000/generate-guide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: user.email, user_prompt: topic }),
      });

      if (response.ok) {
        const data = await response.json();
        setConversation(data.study_guide.conversation); // This will include both prompt and response
        setSelectedStudyGuide(data.study_guide);
        if (data.study_guide.conversation.length > 0) {
          startTypingEffect(data.study_guide.conversation[0].response || "");
        }
        if (onStudyGuideGenerated) {
          onStudyGuideGenerated(data.study_guide.content, topic);
        }
      } else {
        setError("Failed to generate study guide. Please try again.");
      }
    } catch (err) {
      console.error("Fetch error:", err);
      setError("Error communicating with the backend.");
    } finally {
      setIsLoading(false);
    }
  };
    
  
  
  
  // Function to send a follow-up question
  const handleFollowUpSubmit = async (e) => {
    e.preventDefault();
    if (!followUp.trim()) return;

    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/update-guide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: user.email,
          study_guide_id: selectedStudyGuide._id,
          user_prompt: followUp
        }),
      });

      if (response.ok) {
        const data = await response.json();

        // Update conversation with the new Q&A
        const updatedConversation = [
          ...conversation,
          { user_prompt: followUp, response: data.response }
        ];
        setConversation(updatedConversation);
        if (data.response) {
            startTypingEffect(data.response || "");
          }
        // Update the selected study guide in the parent state
        setSelectedStudyGuide(prevGuide => ({
          ...prevGuide,
          conversation: updatedConversation
        }));

        setFollowUp(""); // Clear follow-up input
      } else {
        console.error("Failed to send follow-up question.");
      }
    } catch (err) {
      console.error("Fetch error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`input-form ${isSidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
      <button 
        className={`sidebar-toggle ${isSidebarOpen ? 'open' : 'closed'}`}
        onClick={() => setIsSidebarOpen((prev) => !prev)}
      >
        ☰
      </button>

      <div className="study-guide-output">
        <div className="study-guide-content">
          {/* 🆕 Display user prompts as chat bubbles */}
          {conversation.length > 0 ? (
            conversation.map((entry, index) => (
              <div key={index} className={`message ${index % 2 === 0 ? "bot" : "user"}`}>
                <p className="user-message"><strong>You:</strong> {entry.user_prompt}</p>
                <p className="bot-message"><strong>TooturAI:</strong> <ReactMarkdown>{entry.response}</ReactMarkdown></p>
              </div>
            ))
          ) : (
            <div className="placeholder-container">
                <p className="placeholder-text">Welcome to the Study Guide Generator</p>
                <p className="placeholder-caption">Ask us anything. We'll help you study.</p>
            </div>
          )}
        </div>
      </div>

      {/* New Study Guide Input */}
      {!selectedStudyGuide && (
        <form className="prompt-bar" onSubmit={handleSubmit}>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter a topic..."
            required
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Generating..." : "Generate"}
          </button>
        </form>
      )}

      {/* Follow-up question input */}
      {selectedStudyGuide && (
        <form className="prompt-bar" onSubmit={handleFollowUpSubmit}>
          <input
            type="text"
            value={followUp}
            onChange={(e) => setFollowUp(e.target.value)}
            placeholder="Ask a follow-up question..."
            required
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Thinking..." : "Ask"}
          </button>
        </form>
      )}
    </div>
  );
}

export default InputForm;

// // 
// import React, { useState } from "react";
// import ReactMarkdown from "react-markdown";
// import "./InputForm.css";

// function InputForm({ onStudyGuideGenerated, user, selectedStudyGuide, setSelectedStudyGuide, isSidebarOpen, setIsSidebarOpen }) {
//   const [topic, setTopic] = useState("");
//   const [followUp, setFollowUp] = useState("");
//   const [error, setError] = useState("");
//   const [isLoading, setIsLoading] = useState(false);
//   const [conversation, setConversation] = useState([]);
//   const [displayedText, setDisplayedText] = useState("");
//   const [isHovered, setIsHovered] = useState(false); // Track hover state

//   return (
//     <div className="input-form">
//       {/* Sidebar Toggle Button (☰) - Only on Study Guide Page */}
//       <button
//         className="sidebar-toggle"
//         onClick={() => setIsSidebarOpen(!isSidebarOpen)}
//         onMouseEnter={() => setIsHovered(true)}
//         onMouseLeave={() => setIsHovered(false)}
//       >
//         ☰
//         {isHovered && <span className="tooltip">Open Sidebar</span>}
//       </button>

//       <div className="study-guide-output">
//         {conversation.length > 0 ? (
//           conversation.map((entry, index) => (
//             <div key={index} className={`message ${index % 2 === 0 ? "bot" : "user"}`}>
//               <p className="user-message"><strong>You:</strong> {entry.user_prompt}</p>
//               <p className="bot-message"><strong>TooturAI:</strong> <ReactMarkdown>{entry.response}</ReactMarkdown></p>
//             </div>
//           ))
//         ) : (
//           <p className="placeholder-text">Welcome to the Study Guide Generator.</p>
//         )}
//       </div>

//       {/* New Study Guide Input */}
//       {!selectedStudyGuide && (
//         <form className="prompt-bar" onSubmit={(e) => { e.preventDefault(); }}>
//           <input type="text" value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Enter a topic..." required />
//           <button type="submit" disabled={isLoading}>{isLoading ? "Generating..." : "Generate"}</button>
//         </form>
//       )}

//       {/* Follow-up question input */}
//       {selectedStudyGuide && (
//         <form className="prompt-bar" onSubmit={(e) => { e.preventDefault(); }}>
//           <input type="text" value={followUp} onChange={(e) => setFollowUp(e.target.value)} placeholder="Ask a follow-up question..." required />
//           <button type="submit" disabled={isLoading}>{isLoading ? "Thinking..." : "Ask"}</button>
//         </form>
//       )}
//     </div>
//   );
// }

// export default InputForm;
