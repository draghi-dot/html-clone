"use client";

import React, { useState, useEffect } from "react";

const Dashboard = () => {
  const [loading, setLoading] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [clusters, setClusters] = useState<{ [key: string]: { filename: string; content: string }[] }>({});

  const handleGenerate = async (tier: number) => {
    setLoading(tier);
    setMessage("");
  
    try {
      // Correctly pass tier to the API
      const response = await fetch(`/api/run-script?tier=${tier}`);
      const data = await response.json();
  
      if (data.success) {
        setMessage(`✅ Tier ${tier} generated successfully!`);
        fetchClusters(); // Refresh clusters after generating
      } else {
        setMessage(`❌ Error: ${data.error}`);
      }
    } catch (error) {
      setMessage(`❌ Request failed: ${error}`);
    }
  
    setLoading(null);
  };
  

  const fetchClusters = async () => {
    try {
      const response = await fetch("/api/get-clusters");
      const data = await response.json();
      if (data.success) {
        setClusters(data.clusters); // Store clusters data
      } else {
        console.error("Error fetching clusters:", data.error);
      }
    } catch (error) {
      console.error("Failed to fetch clusters:", error);
    }
  };

  useEffect(() => {
    fetchClusters(); // Fetch clusters on page load
  }, []);

  return (
    <div className="h-screen w-screen grid grid-cols-2 grid-rows-2 gap-4 p-6 bg-gray-100 font-sans">
      {/* Buttons */}
      {[1, 2, 3, 4].map((tier) => (
        <button
          key={tier}
          onClick={() => handleGenerate(tier)}
          className={`p-6 rounded-lg shadow-md text-white text-4xl font-extrabold tracking-wide transition-transform transform hover:scale-105 active:scale-95 ${
            tier === 1 ? "bg-green-500" : tier === 2 ? "bg-orange-300" : tier === 3 ? "bg-orange-600" : "bg-red-500"
          }`}
        >
          {loading === tier ? "Processing..." : `Generate Tier ${tier}`}
        </button>
      ))}

      {/* Display Message */}
      {message && (
        <div className="absolute bottom-5 left-1/2 transform -translate-x-1/2 bg-white p-4 rounded shadow-md text-lg font-semibold">
          {message}
        </div>
      )}

      {/* Display Clusters */}
      <div className="col-span-2 mt-8 bg-white p-4 rounded shadow-md max-h-96 overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4">Cluster Output</h2>
        {Object.entries(clusters).length === 0 ? (
          <p>No clusters to display</p>
        ) : (
          Object.entries(clusters).map(([tier, files]) => (
            <div key={tier} className="mb-6">
              <h3 className="text-xl font-semibold text-blue-600">{tier}</h3>
              <ul className="list-disc pl-5">
                {files.map(({ filename, content }) => (
                  <li key={filename} className="mt-2">
                    <strong>{filename}:</strong>
                    <pre className="bg-gray-200 p-2 rounded mt-1">{content}</pre>
                  </li>
                ))}
              </ul>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Dashboard;
