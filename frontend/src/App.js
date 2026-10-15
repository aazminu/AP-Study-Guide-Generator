import React, { useState, useEffect } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import WelcomePage from "./components/WelcomePage";
import SignupForm from "./components/SignUpForm";
import HomePage from "./components/HomePage";
import InputForm from "./components/InputForm";
import Sidebar from "./components/Sidebar";
import TopNavbar from "./components/TopNavbar";

const clientId = "881037752146-jhiu2q74gfkkj7phe2034p53m3nd5k6c.apps.googleusercontent.com";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isProfileComplete, setIsProfileComplete] = useState(false);
  const [user, setUser] = useState(null);
  const [currentPage, setCurrentPage] = useState("home");
  const [errorMessage, setErrorMessage] = useState("");
  const [studyGuide, setStudyGuide] = useState("");
  const [history, setHistory] = useState([]); 
  const [selectedStudyGuide, setSelectedStudyGuide] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true); // 🔹 Sidebar state
// Store previous study guides

useEffect(() => {
  if (currentPage === "studyGuide") {
    setIsSidebarOpen(false); // ✅ Fix: Close sidebar initially
  } else {
    setIsSidebarOpen(true); // ✅ Fix: Sidebar open by default elsewhere
  }
}, [currentPage]);

  const handleLoginSuccess = (user) => {
    setIsAuthenticated(true);
    setIsProfileComplete(true);
    setUser(user);
    setCurrentPage("home");
    setErrorMessage("");
  };

  const handleSignupSuccess = (user) => {
    setIsAuthenticated(true);
    setIsProfileComplete(false);
    setUser(user);
    setCurrentPage("signup");
    setErrorMessage("");
  };

  const handleProfileSubmit = async (profileData) => {
    const newUser = { ...user, ...profileData };

    try {
      const response = await fetch("http://localhost:8000/api/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newUser),
      });

      if (response.ok) {
        setIsProfileComplete(true);
        setCurrentPage("home");
      } else {
        setErrorMessage("Failed to save profile. Please try again.");
      }
    } catch (error) {
      console.error("Error saving profile:", error);
      setErrorMessage("Error saving profile. Please try again.");
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setIsProfileComplete(false);
    setUser(null);
    setCurrentPage("home");
    setErrorMessage("");
  };

  // Store generated study guides
  // const handleStudyGuideGenerated = (generatedText) => {
  //   const newEntry = { topic: generatedText.slice(0, 20) + "...", studyGuide: generatedText };
  //   setHistory((prevHistory) => [...prevHistory, newEntry]);
  //   setStudyGuide(generatedText);
  // };
  const handleStudyGuideGenerated = async (generatedText, topic) => {
    const newEntry = { title: topic, content: generatedText };
  
    // Update sidebar history **immediately**
    setHistory((prevHistory) => [...prevHistory, newEntry]);
  
    // Save to the database
    await saveStudyGuideToDB(topic, generatedText);
  
    // Fetch updated study guides **immediately** so the sidebar updates
    fetchStudyGuides();
  
    setStudyGuide(generatedText);
  };
  // Function to save study guide to database
  const saveStudyGuideToDB = async (title, content) => {
    if (!user || !user.email) {
      console.error("User email is missing. Cannot save study guide.");
      return;
    }
  
    try {
      const response = await fetch(`http://localhost:8000/api/save-study-guide?email=${user.email}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: user.email, title: title, content: content }),
      });
  
      if (!response.ok) {
        throw new Error("Failed to save study guide.");
      }
  
      console.log("Study guide successfully saved!");
  
      // After saving, immediately update history
      fetchStudyGuides(); // 🆕 Fetch latest study guides after saving
  
    } catch (error) {
      console.error("Error saving study guide:", error);
    }
  };
  
  // 🆕 Function to fetch the latest study guides from the backend
  const fetchStudyGuides = async () => {
    if (!user || !user.email) return;
  
    try {
      const response = await fetch(`http://localhost:8000/api/get-study-guides?email=${user.email}`);
      const data = await response.json();
  
      if (data.study_guides) {
        setHistory(data.study_guides); // ✅ Update study guide list in sidebar immediately
      }
    } catch (error) {
      console.error("Error fetching study guides:", error);
    }
  };
  
  
  // Call fetchStudyGuides when the user logs in to ensure latest history is loaded
  useEffect(() => {
    if (user) {
      fetchStudyGuides();
    }
  }, [user]);
  

  // Load a past study guide
  const handleLoadStudyGuide = (selectedGuide) => {
    setStudyGuide(selectedGuide.content);
    setCurrentPage("studyGuide");
  };

  const renderPage = () => {
    if (!isAuthenticated) {
      return (
        <WelcomePage
          onLoginSuccess={handleLoginSuccess}
          onSignupSuccess={handleSignupSuccess}
          errorMessage={errorMessage}
          setErrorMessage={setErrorMessage}
        />
      );
    }
  
    if (!isProfileComplete) {
      return <SignupForm onSubmit={handleProfileSubmit} />;
    }
  
    switch (currentPage) {
      case "studyGuide":
        return (
          <InputForm
            onStudyGuideGenerated={handleStudyGuideGenerated}
            studyGuide={studyGuide}
            user={user}
            selectedStudyGuide={selectedStudyGuide}
            setSelectedStudyGuide={setSelectedStudyGuide} // ✅ Pass setter to update conversation
            isSidebarOpen={isSidebarOpen} // 🔹 Pass sidebar state
            setIsSidebarOpen={setIsSidebarOpen}
          />
        );
      case "home":
        return (
          <HomePage
            onNavigate={(page) => {
              if (page === "studyGuide") {
                setSelectedStudyGuide(null);
                setStudyGuide("");
              }
              setCurrentPage(page);
            }}
            setSelectedStudyGuide={setSelectedStudyGuide}
            isSidebarOpen={isSidebarOpen}
          />
        );
      default:
        return <HomePage onNavigate={setCurrentPage} />;
    }
  };
  

  return (
    <GoogleOAuthProvider clientId={clientId}>
      <div className={`app ${isSidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
        {isAuthenticated && isProfileComplete && (
          <Sidebar
            onNavigate={setCurrentPage}
            onSelectHistory={setSelectedStudyGuide}  // ✅ Load clicked study guide
            onLogout={handleLogout}
            user={user}
            history={history}
            currentPage={currentPage}
            isSidebarOpen={isSidebarOpen}
            setIsSidebarOpen={setIsSidebarOpen}
          />
        )}
        <div className={`main-content ${!isAuthenticated ? "centered" : ""}${isSidebarOpen ? "with-sidebar" : "full-width"}`}>
          {renderPage()}
        </div>
      </div>
    </GoogleOAuthProvider>
  );
}

export default App;
