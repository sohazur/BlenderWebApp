import React, { useState } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);

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

      alert("File uploaded successfully: " + response.data.status);
    } catch (error) {
      alert("Error uploading file");
    }
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
    </div>
  );
}

export default App;
