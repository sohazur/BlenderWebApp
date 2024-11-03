import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css"; // Import CSS for styling

function App() {
  const [file, setFile] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState("Idle");
  const [downloadLinks, setDownloadLinks] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    setIsUploading(true);
    setStatus("Uploading...");

    try {
      const response = await axios.post(
        "http://localhost:5001/upload",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      setTaskId(response.data.task_id);
      setStatus("Processing...");
      setDownloadLinks([]);
    } catch (error) {
      console.error("Error uploading file", error);
      setStatus("Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  useEffect(() => {
    const checkStatus = async () => {
      if (taskId) {
        try {
          const response = await axios.get(
            `http://localhost:5001/status/${taskId}`
          );

          if (response.data.status === "completed") {
            setStatus("Rendering complete");
            setDownloadLinks(
              response.data.file_paths.map(
                (path) => `http://localhost:5001${path}`
              )
            );
          } else if (response.data.status === "pending") {
            setStatus("Processing...");
          } else if (response.data.status === "failed") {
            setStatus(`Rendering failed: ${response.data.error}`);
          }
        } catch (error) {
          console.error("Error checking status", error);
          setStatus("Error checking status");
        }
      }
    };

    const interval = setInterval(checkStatus, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [taskId]);

  return (
    <div className="app-container">
      <h1 className="title">RaByte Renderer</h1>
      <div className="upload-container">
        <input type="file" onChange={handleFileChange} className="file-input" />
        <button
          onClick={handleUpload}
          className="upload-button"
          disabled={isUploading || !file}
        >
          {isUploading ? "Uploading..." : "Upload"}
        </button>
        {status === "Processing..." && <div className="progress-bar"></div>}
      </div>
      <p className="status-text">{status}</p>
      {downloadLinks.length > 0 && (
        <div className="download-links">
          {downloadLinks.map((link, index) => (
            <a
              href={link}
              download={`Rendered_Image_${index + 1}.jpg`}
              key={index}
              className="download-link"
            >
              Download Result {index + 1}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
