import React, { useState, useEffect } from "react";
import { useGoogleLogin } from "@react-oauth/google";
import "./WelcomePage.css";

function WelcomePage({ onLoginSuccess, onSignupSuccess, errorMessage, setErrorMessage }) {
  const [titleText, setTitleText] = useState(""); // Start with an empty string
  const fullTitle = "Welcome to Tootur.";

  useEffect(() => {
    let index = 0; // Start index at 0
    const interval = setInterval(() => {
      if (index <= fullTitle.length) {
        setTitleText(fullTitle.slice(0, index)); // Update titleText with a slice of fullTitle
        index++;
      } else {
        clearInterval(interval); // Stop typing effect once complete
      }
    }, 100); // Adjust typing speed here (ms per character)

    return () => clearInterval(interval); // Cleanup on component unmount
  }, []); // Empty dependency array to run only on mount

  const login = useGoogleLogin({
    onSuccess: async (response) => {
      try {
        const userInfo = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", {
          headers: { Authorization: `Bearer ${response.access_token}` },
        });
        const user = await userInfo.json();

        const checkResponse = await fetch(
          `http://localhost:8000/api/users/check?email=${user.email}`
        );
        const checkData = await checkResponse.json();

        if (checkData.exists) {
          onLoginSuccess(user);
        } else {
          setErrorMessage("You do not have an account yet. Please sign up.");
        }
      } catch (error) {
        console.error("Error during login process:", error);
        setErrorMessage("An error occurred during login. Please try again.");
      }
    },
    onError: (error) => {
      console.error("Login failed:", error);
      setErrorMessage("Login failed. Please try again.");
    },
  });

  const signup = useGoogleLogin({
    onSuccess: async (response) => {
      try {
        const userInfo = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", {
          headers: { Authorization: `Bearer ${response.access_token}` },
        });
        const user = await userInfo.json();

        const checkResponse = await fetch(
          `http://localhost:8000/api/users/check?email=${user.email}`
        );
        const checkData = await checkResponse.json();

        if (checkData.exists) {
          setErrorMessage("Oops! Looks like you already have an account. Please log in instead:)");
        } else {
          onSignupSuccess(user);
        }
      } catch (error) {
        console.error("Error during signup process:", error);
        setErrorMessage("An error occurred during signup. Please try again.");
      }
    },
    onError: (error) => {
      console.error("Signup failed:", error);
      setErrorMessage("Signup failed. Please try again.");
    },
  });

  return (
    <div className="welcome-page full-width">
      <nav className="top-navbar">
        <div className="nav-container">
          <div className="nav-logo">Tootur</div>
          <div className="nav-links">
            <a href="#about">About Us</a>
            <a href="#contact">Contact Us</a>
            <button onClick={() => login()}>Login</button>
            <button onClick={() => signup()}>Sign Up</button>
          </div>
        </div>
      </nav>
      <div className="welcome-content">
        <h1 className="sour-gummy-ali">{titleText}</h1>
        <p className="para">Please log in or sign up to get started.</p>
        {errorMessage && <p className="error-message">{errorMessage}</p>}
      </div>
    </div>
  );
}

export default WelcomePage;
