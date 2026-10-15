import React, { useState } from "react";
import "./WelcomePage.css";

function SignupForm({ onSubmit, errorMessage }) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    role: "",
    educationLevel: "",
    usagePurpose: "",
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (

    <div className="signup-form">
      <h2>Create Your Profile</h2>
      {errorMessage && <p className="error">{errorMessage}</p>}
      <form onSubmit={handleSubmit}>
        <label>
          Name    
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />
        </label>

        <label>
          Email
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
          />
        </label>

        <label>
          Are you a
          <select name="role" value={formData.role} onChange={handleChange}>
            <option value="">Select...</option>
            <option value="student">Student</option>
            <option value="teacher">Teacher</option>
            <option value="other">Other</option>
          </select>
        </label>

        <label>
          Education Level
          <select
            name="educationLevel"
            value={formData.educationLevel}
            onChange={handleChange}
          >
            <option value="">Select...</option>
            <option value="high school">High School</option>
            <option value="undergraduate">Undergraduate</option>
            <option value="postgraduate">Postgraduate</option>
          </select>
        </label>

        <label>
          What are you using Tootur for?
          <textarea
            name="usagePurpose"
            value={formData.usagePurpose}
            onChange={handleChange}
            placeholder="Describe your purpose..."
          />
        </label>

        <button type="submit">Sign Up</button>
      </form>
    </div>
  );
}

export default SignupForm;
