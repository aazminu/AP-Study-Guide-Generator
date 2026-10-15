// import React, { useState } from "react";
// import { GoogleLogin } from "@react-oauth/google";
// import "./login.css"; // Add this file for styling

// const Login = ({ onLoginSuccess }) => {
//   const [isDropdownVisible, setDropdownVisible] = useState(false);

//   const handleLoginSuccess = (credentialResponse) => {
//     console.log("Login Success:", credentialResponse);
//     onLoginSuccess(credentialResponse);
//     setDropdownVisible(false); // Hide dropdown after login
//   };

//   const handleLoginError = () => {
//     console.error("Login Failed");
//   };

//   return (
//     <div
//       className="login-container"
//       onMouseEnter={() => setDropdownVisible(true)}
//       onMouseLeave={() => setDropdownVisible(false)}
//     >
//       <button className="login-text">Login</button>
//       {isDropdownVisible && (
//         <div className="login-dropdown">
//           <GoogleLogin
//             onSuccess={handleLoginSuccess}
//             onError={handleLoginError}

//           />
//         </div>
//       )}
//     </div>
//   );
// };

// export default Login;


import React from "react";
import { googleLogout, useGoogleLogin } from "@react-oauth/google";

function Login({ onLoginSuccess }) {
  const login = useGoogleLogin({
    onSuccess: async (response) => {
      // Fetch user profile from Google
      const userInfo = await fetch(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        {
          headers: { Authorization: `Bearer ${response.access_token}` },
        }
      );
      const user = await userInfo.json();

      // Send user data to the backend
      try {
        const backendResponse = await fetch("http://localhost:8000/api/users", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: user.name,
            email: user.email,
          }),
        });

        if (backendResponse.ok) {
          const data = await backendResponse.json();
          console.log("User successfully stored:", data);
          if (onLoginSuccess) onLoginSuccess(user); // Notify parent component
        } else {
          console.error("Failed to store user in the backend.");
        }
      } catch (error) {
        console.error("Error while sending user data to the backend:", error);
      }
    },
    onError: (error) => {
      console.error("Login failed:", error);
    },
  });

  return (
    <div>
      <button onClick={() => login()}>Login</button>
    </div>
  );
}

export default Login;
