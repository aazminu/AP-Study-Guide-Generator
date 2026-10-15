import React from "react";
import { googleLogout } from "@react-oauth/google";

function Logout({ onLogoutSuccess }) {
  const handleLogout = () => {
    googleLogout(); // Clears the Google session
    if (onLogoutSuccess) onLogoutSuccess(); // Notify parent component
    console.log("User logged out successfully.");
  };

  return <button onClick={handleLogout}>Logout</button>;
}

export default Logout;