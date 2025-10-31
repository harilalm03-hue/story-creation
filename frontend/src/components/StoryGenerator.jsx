import { useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config";

function StoryGenerator() {
  const [prompt, setPrompt] = useState("");
  const [story, setStory] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const generateStory = async () => {
    if (!prompt.trim()) {
      setError("Please enter a prompt!");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setStory("");

      const createResponse = await axios.post(`${API_BASE_URL}/stories/create`, {
        theme: prompt,
      });

      const jobId = createResponse.data.job_id;

      let completed = false;
      let result = null;

      while (!completed) {
        await new Promise((r) => setTimeout(r, 1500));
        const jobResponse = await axios.get(`${API_BASE_URL}/job/jobs/${jobId}`);
        if (jobResponse.data.status === "completed") {
          completed = true;
          
          result =
            jobResponse.data.story?.content ||
            jobResponse.data.content ||
  JSON.stringify(jobResponse.data, null, 2);

        } else if (jobResponse.data.status === "failed") {
          throw new Error(jobResponse.data.error || "Story generation failed.");
        }
      }

      setStory(result);
    } catch (err) {
      console.error(err);
      setError("Failed to generate story. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="story-generator">
      <h2>Type a story prompt</h2>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Example: A robot learns to love..."
        rows={5}
        style={{ width: "100%", padding: "10px", borderRadius: "8px" }}
      />
      <button onClick={generateStory} disabled={loading} style={{ marginTop: 10 }}>
        {loading ? "Generating..." : "Generate Story"}
      </button>

      {error && <p style={{ color: "red", marginTop: 10 }}>{error}</p>}

      {story && (
        <div style={{ marginTop: 20, padding: 10, background: "#f4f4f4", borderRadius: 8 }}>
          <h3>Your Story:</h3>
          <pre style={{ whiteSpace: "pre-wrap" }}>{story}</pre>
        </div>
      )}
    </div>
  );
}

export default StoryGenerator;
