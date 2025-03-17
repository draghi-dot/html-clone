"use client";

import React, { useState } from "react";

const Dashboard = () => {
  const [loading, setLoading] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [clusters, setClusters] = useState<{ [key: string]: { filename: string; content: string }[] }>({});
  const [showClusters, setShowClusters] = useState(false);
  const [selectedTier, setSelectedTier] = useState<string | null>(null);

  const handleGenerate = async (tier: number) => {
    setLoading(tier);
    setMessage("");
    setShowClusters(false);
    setSelectedTier(`Tier ${tier}`);

    try {
      const response = await fetch(`/api/run-script?tier=${tier}`);
      const data = await response.json();

      console.log("API Response from run-script:", data);

      if (data?.success) {
        setMessage(`✅ Tier ${tier} generated successfully!`);
        fetchClusters();
      } else {
        setMessage(`❌ Error: ${data?.error || "Unknown error"}`);
      }
    } catch (error) {
      console.error("Error in handleGenerate:", error);

      if (error instanceof Error) {
        setMessage(`❌ Request failed: ${error.message}`);
      } else {
        setMessage("❌ Request failed: Unknown error");
      }
    }

    setLoading(null);
  };

  const fetchClusters = async () => {
    try {
      const response = await fetch("/api/get-clusters");
      const data = await response.json();

      console.log("API Response from get-clusters:", data);

      if (data?.success && data?.clusters) {
        setClusters(data.clusters);
        setShowClusters(true);
      } else {
        console.error("Error fetching clusters:", data?.error || "Unknown error");
      }
    } catch (error) {
      console.error("Error in fetchClusters:", error);

      if (error instanceof Error) {
        console.error("Failed to fetch clusters:", error.message);
      } else {
        console.error("Failed to fetch clusters: Unknown error");
      }
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100 font-sans text-black">
      <div className="flex justify-between p-6 h-[30%]">
        {[1, 2, 3, 4].map((tier) => (
          <button
            key={tier}
            onClick={() => handleGenerate(tier)}
            className={`p-6 rounded-lg shadow-md text-white text-4xl font-extrabold tracking-wide transition-transform transform hover:scale-105 active:scale-95 ${
              tier === 1
                ? "bg-green-500"
                : tier === 2
                ? "bg-orange-300"
                : tier === 3
                ? "bg-orange-600"
                : "bg-red-500"
            }`}
          >
            {loading === tier ? "Processing..." : `Generate Tier ${tier}`}
          </button>
        ))}
      </div>

      {message && (
        <div className="absolute bottom-5 left-1/2 transform -translate-x-1/2 bg-white p-4 rounded shadow-md text-lg font-semibold">
          {message}
        </div>
      )}

      <div className="flex-1 p-6 overflow-y-auto">
        {showClusters && selectedTier && clusters[selectedTier] && (
          <div className="bg-white p-4 rounded shadow-md max-h-[calc(100vh-30%)]">
            <h2 className="text-2xl font-bold mb-4">Cluster Output for {selectedTier}</h2>
            {clusters[selectedTier].length === 0 ? (
              <p>No clusters to display for {selectedTier}</p>
            ) : (
              <ul className="list-disc pl-5">
                {clusters[selectedTier].map(({ filename, content }) => (
                  <li key={filename} className="mt-2">
                    <strong>{filename}:</strong>
                    <pre className="bg-gray-200 p-2 rounded mt-1">{content}</pre>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
