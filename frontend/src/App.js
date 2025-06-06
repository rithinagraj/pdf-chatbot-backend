import React, { useState, useRef } from "react";
import "./App.css";

const BACKEND_URL = "https://pdf-chatbot-backend-4o8b.onrender.com";

function App() {
  const [pdfFileName, setPdfFileName] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [query, setQuery] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [loadingAnswer, setLoadingAnswer] = useState(false);

  const fileInputRef = useRef();

  // Upload handler
  async function handleUpload(e) {
    e.preventDefault();
    setUploadError("");

    if (!fileInputRef.current.files.length) {
      setUploadError("Please select a PDF file to upload.");
      return;
    }

    const file = fileInputRef.current.files[0];
    const formData = new FormData();
    formData.append("pdf", file);

    setUploading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (res.ok) {
        setPdfFileName(data.filename);
        setChatHistory([]);
      } else {
        setUploadError(data.error || "Failed to upload PDF.");
      }
    } catch (err) {
      setUploadError("Server error. Try again.");
    } finally {
      setUploading(false);
    }
  }

  // Chat submission
  async function handleChatSubmit(e) {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage = { sender: "user", text: query };
    setChatHistory((prev) => [...prev, userMessage]);
    setLoadingAnswer(true);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      const data = await res.json();

      const botMessage = {
        sender: "bot",
        text: res.ok ? data.answer || "No answer found." : data.error || "Error fetching answer.",
      };

      setChatHistory((prev) => [...prev, botMessage]);
    } catch (err) {
      setChatHistory((prev) => [...prev, { sender: "bot", text: "Server error. Try again." }]);
    } finally {
      setLoadingAnswer(false);
      setQuery("");
    }
  }

  return (
    <div className="app-container">
      {!pdfFileName ? (
        <div className="landing-page">
          <form className="upload-form" onSubmit={handleUpload}>
            <h1>Smart PDF Assistant</h1>
            <p>Upload a PDF and ask questions about it instantly!</p>
            <input type="file" accept="application/pdf" ref={fileInputRef} disabled={uploading} />
            <button type="submit" disabled={uploading}>
              {uploading ? "Uploading..." : "Upload PDF"}
            </button>
            {uploadError && <p className="error-msg">{uploadError}</p>}
          </form>
        </div>
      ) : (
        <div className="main-content">
          <div className="pdf-viewer">
            <iframe
              title="PDF Viewer"
              src={`${BACKEND_URL}/pdf/${encodeURIComponent(pdfFileName)}`}
              frameBorder="0"
            />
          </div>

          <div className="chatbot">
            <div className="chat-messages">
              {chatHistory.length === 0 && (
                <p className="empty-msg">Ask any question about the PDF you uploaded!</p>
              )}
              {chatHistory.map((msg, idx) => (
                <div key={idx} className={`chat-message ${msg.sender}`}>
                  {msg.text}
                </div>
              ))}
              {loadingAnswer && <p className="loading-msg">Assistant is typing...</p>}
            </div>

            <form onSubmit={handleChatSubmit} className="chat-input-form">
              <input
                type="text"
                className="chat-input"
                placeholder="Type your question..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={loadingAnswer}
              />
              <button type="submit" className="chat-submit" disabled={loadingAnswer || !query.trim()}>
                Send
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
