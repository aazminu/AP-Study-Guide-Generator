import React, { useState, useEffect } from "react";
import "./HomePage.css";

function HomePage({ onNavigate, setSelectedStudyGuide, isSidebarOpen }) {
  const titles = [
    "Got an exam coming up?",
    "Not sure where to start studying?",
    "You've come to the right place!",
  ];
  
  const [currentTitle, setCurrentTitle] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [charIndex, setCharIndex] = useState(0);
  const [speed, setSpeed] = useState(100); // Typing/erasing speed

  useEffect(() => {
    const handleTyping = () => {
      const fullText = titles[currentIndex];
      if (isDeleting) {
        if (charIndex > 0) {
          setCurrentTitle(fullText.substring(0, charIndex - 1));
          setCharIndex(charIndex - 1);
          setSpeed(30); // Erasing speed
        } else {
          setIsDeleting(false);
          setCurrentIndex((currentIndex + 1) % titles.length);
          setSpeed(1000); // Pause before typing the next title
        }
      } else {
        if (charIndex < fullText.length) {
          setCurrentTitle(fullText.substring(0, charIndex + 1));
          setCharIndex(charIndex + 1);
          setSpeed(20); // Typing speed
        } else {
          setIsDeleting(true);
          setSpeed(2000); // Pause after completing the title
        }
      }
    };

    const typingTimeout = setTimeout(handleTyping, speed);

    return () => clearTimeout(typingTimeout);
  }, [charIndex, isDeleting, currentIndex, speed, titles]);

  return (
    <div className={`home-page ${isSidebarOpen ? 'sidebar-open' : ''}`}>
      <h1 className="rotating-title">{currentTitle}</h1>
      <div className="options">
      <button onClick={() => {
    setSelectedStudyGuide(null); // Reset study guide
    onNavigate("studyGuide");
}}>
  Generate New Study Guide
</button>
        <button onClick={() => onNavigate("flashcards")}>Flashcards</button>
        <button onClick={() => onNavigate("studyPlan")}>Study Plan</button>
        <button onClick={() => onNavigate("practiceTests")}>Generate Practice Tests</button>
      </div>
    </div>
  );
}

export default HomePage;
