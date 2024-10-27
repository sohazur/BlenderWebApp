import React, { useState, useEffect } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState("");
  const [downloadLink, setDownloadLink] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        "https://3b7e-87-200-119-69.ngrok-free.app/upload",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      setTaskId(response.data.task_id);
      setStatus("Processing...");
    } catch (error) {
      alert("Error uploading file");
    }
  };

  useEffect(() => {
    const checkStatus = async () => {
      if (taskId) {
        try {
          const response = await axios.get(
            `https://3b7e-87-200-119-69.ngrok-free.app/status/${taskId}`
          );
          if (response.data.status === "completed") {
            setStatus("Rendering complete");
            setDownloadLink(
              `https://3b7e-87-200-119-69.ngrok-free.app/renders/${file.name}`
            ); // Update with actual file path
          } else if (response.data.status === "pending") {
            setStatus("Processing...");
          } else if (response.data.status === "failed") {
            setStatus("Rendering failed: " + response.data.error);
          }
        } catch (error) {
          console.error("Error checking status", error);
        }
      }
    };

    const interval = setInterval(checkStatus, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [taskId]);

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      <p>Status: {status}</p>
      {downloadLink && (
        <a href={downloadLink} download>
          Download Result
        </a>
      )}
    </div>
  );
}

export default App;
