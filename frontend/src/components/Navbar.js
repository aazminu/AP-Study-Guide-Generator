import React from "react";

function Navbar() {
  return (
    <nav style={navbarStyles}>
      <div style={logoStyles}>TooturAI</div>
    </nav>
  );
}

const navbarStyles = {
  backgroundColor: "#343541",
  color: "white",
  padding: "10px 20px",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  boxShadow: "0 2px 4px rgba(0, 0, 0, 0.2)",
};

const logoStyles = {
  fontSize: "20px",
  fontWeight: "bold",
};

export default Navbar;