import React from "react";
import "./TopNavbar.css";

function TopNavbar({ showAuthButtons }) {
  return (
    <nav className="top-navbar">
      <div className="nav-container">
        <div className="nav-logo">Tootur</div>
        <div className="nav-links">
          <a href="#about">About Us</a>
          <a href="#contact">Contact Us</a>
          {showAuthButtons && (
            <>
              <button>Login</button>
              <button>Signup</button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

export default TopNavbar;
