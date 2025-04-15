import React, { useState } from "react";

const QAInterface = () => {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [chunks, setChunks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch("/api/query/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ q: query, k: 5 }), // Adjust the parameters as needed
      });

      const data = await response.json();
      setAnswer(data.answer);
      setChunks(data.chunks);
    } catch (error) {
      console.error("Error fetching answer:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Q&A Interface</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Ask your question here"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          required
          disabled={loading}
        />
        <button type="submit" disabled={loading} style={{ position: 'relative' }}>
          {loading ? (
            <>
              <span style={{ visibility: 'hidden' }}>Ask</span>
              <span style={{ 
                position: 'absolute', 
                top: '50%', 
                left: '50%', 
                transform: 'translate(-50%, -50%)',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}>
                <span className="loader" style={{
                  width: '12px',
                  height: '12px',
                  border: '2px solid #fff',
                  borderBottom: '2px solid transparent',
                  borderRadius: '50%',
                  display: 'inline-block',
                  animation: 'rotation 1s linear infinite'
                }}></span>
                Loading...
              </span>
            </>
          ) : "Ask"}
        </button>
      </form>

      {loading && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          margin: '20px 0',
          gap: '10px' 
        }}>
          <div className="loader" style={{
            width: '20px',
            height: '20px',
            border: '3px solid #ccc',
            borderBottom: '3px solid #1976d2',
            borderRadius: '50%',
            display: 'inline-block',
            animation: 'rotation 1s linear infinite'
          }}></div>
          <p>Generating answer...</p>
        </div>
      )}

      {answer && !loading && (
        <div>
          <h3>Answer:</h3>
          <p>{answer}</p>
        </div>
      )}

      {chunks.length > 0 && !loading && (
        <div>
          <h3>Relevant Document Excerpts:</h3>
          {chunks.map((chunk, index) => (
            <div key={index}>
              <p>{chunk.chunk_text}</p>
            </div>
          ))}
        </div>
      )}

      <style>
        {`
          @keyframes rotation {
            0% {
              transform: rotate(0deg);
            }
            100% {
              transform: rotate(360deg);
            }
          }
        `}
      </style>
    </div>
  );
};

export default QAInterface;