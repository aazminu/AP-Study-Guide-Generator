import React, { useEffect, useState, useRef } from "react";
import ReactDOM from "react-dom";
import "./Sidebar.css";

function Sidebar({ onNavigate, onSelectHistory, onLogout, user, currentPage, setSelectedStudyGuide, history, isSidebarOpen, setIsSidebarOpen }) {
  const [studyGuides, setStudyGuides] = useState([]);
  const [menuVisible, setMenuVisible] = useState(null); // Track which guide has options open
  const [editMode, setEditMode] = useState(null); // Track renaming state
  const [newTitle, setNewTitle] = useState(""); // Store new title input
  const menuRef = useRef(null); // Reference for detecting outside clicks

  // Fetch user's study guides from the backend
  useEffect(() => {
    if (user) {
      fetch(`http://localhost:8000/api/get-study-guides?email=${user.email}`)
        .then((response) => response.json())
        .then((data) => {
          setStudyGuides(data.study_guides || []);
        })
        .catch((error) => console.error("Error fetching study guides:", error));
    }
  }, [user, history]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuVisible(null); // Close menu if clicking outside
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Add click-away handler
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuVisible(null); // Close the dropdown
      }
    }

    // Add event listener when dropdown is open
    if (menuVisible !== null) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    // Cleanup
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [menuVisible]);

  // Handle renaming a study guide
  const handleRename = async (studyGuideId) => {
    if (!newTitle.trim()) return;

    try {
      const response = await fetch("http://localhost:8000/api/rename-study-guide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: user.email,
          study_guide_id: studyGuideId,
          new_title: newTitle,
        }),
      });

      if (response.ok) {
        setStudyGuides((prevGuides) =>
          prevGuides.map((guide) =>
            guide._id === studyGuideId ? { ...guide, title: newTitle } : guide
          )
        );
        setEditMode(null);
        setNewTitle("");
        setMenuVisible(null);
      } else {
        console.error("Failed to rename study guide.");
      }
    } catch (err) {
      console.error("Fetch error:", err);
    }
  };

  // Handle deleting a study guide
  const handleDelete = async (studyGuideId) => {
    try {
      const response = await fetch("http://localhost:8000/api/delete-study-guide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: user.email,
          study_guide_id: studyGuideId,
        }),
      });

      if (response.ok) {
        setStudyGuides((prevGuides) =>
          prevGuides.filter((guide) => guide._id !== studyGuideId)
        );
        setMenuVisible(null); // Close menu after deleting
      } else {
        console.error("Failed to delete study guide.");
      }
    } catch (err) {
      console.error("Fetch error:", err);
    }
  };

  // Add this function to calculate dropdown position
  const getDropdownPosition = (buttonElement) => {
    if (!buttonElement) return {};
    const rect = buttonElement.getBoundingClientRect();
    return {
      top: rect.top,
      left: 260, // Sidebar width
    };
  };

  // Modify the render of dropdown menu
  const renderDropdown = (guide) => {
    if (menuVisible !== guide._id) return null;

    return ReactDOM.createPortal(
      <div 
        className="dropdown-menu" 
        ref={menuRef}
        style={getDropdownPosition(document.querySelector(`[data-guide-id="${guide._id}"]`))}
      >
        <span onClick={() => {
          setEditMode(guide._id);
          setNewTitle(guide.title);
          setMenuVisible(null);
        }}>
          Rename
        </span>
        <span onClick={() => handleDelete(guide._id)}>
          Delete
        </span>
      </div>,
      document.body
    );
  };

  return (
    <div className={`sidebar ${!isSidebarOpen ? "closed" : ""}`}>
      <button 
        className="sidebar-toggle"
        onClick={() => setIsSidebarOpen((prev) => !prev)}
      >
        ☰
      </button>
      <ul className="nav-links-side">
        <li onClick={() => onNavigate("home")}>Home</li>
        <li
          onClick={() => {
            onSelectHistory(null);
            onNavigate("studyGuide");
          }}
        >
          New Study Guide
        </li>

        <li onClick={() => onNavigate("flashcards")}>Flashcards</li>
        <li onClick={() => onNavigate("studyPlan")}>Study Plan</li>
        <li onClick={() => onNavigate("practiceTests")}>Practice Tests</li>
        <li className="logout" onClick={onLogout}>
          Logout
        </li>

        {/* Display past study guides with delete & rename options */}
        {studyGuides.length > 0 && currentPage === "studyGuide" && (
          <div className="history-section">
            <h3 className="history-title">Activity</h3>
            <ul className="history-list">
              {studyGuides.map((guide) => (
                <li 
                  key={guide._id} 
                  className="history-item"
                  onClick={() => onSelectHistory(guide)}
                >
                  <div className="study-guide-container">
                    {editMode === guide._id ? (
                      <input
                        type="text"
                        value={newTitle}
                        onChange={(e) => setNewTitle(e.target.value)}
                        onBlur={() => handleRename(guide._id)}
                        onKeyDown={(e) => e.key === "Enter" && handleRename(guide._id)}
                        className="rename-input"
                        autoFocus
                        onClick={(e) => e.stopPropagation()}
                      />
                    ) : (
                      <span>{guide.title}</span>
                    )}
                    
                    <button
                      className="menu-button"
                      data-guide-id={guide._id}
                      onClick={(e) => {
                        e.stopPropagation();
                        setMenuVisible(menuVisible === guide._id ? null : guide._id);
                      }}
                    >
                      ⋮
                    </button>
                  </div>
                  {renderDropdown(guide)}
                </li>
              ))}
            </ul>
          </div>
        )}
      </ul>
    </div>
  );
}

export default Sidebar;


