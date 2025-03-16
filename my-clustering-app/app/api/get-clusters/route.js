import { NextResponse } from "next/server";
import { exec } from "child_process";
import path from "path";
import fs from "fs";

// API route to run the Python script
export async function GET(req) {
  const { searchParams } = new URL(req.url);
  const tier = searchParams.get("tier");

  if (!tier || !["1", "2", "3", "4"].includes(tier)) {
    return NextResponse.json({ success: false, error: "Invalid tier parameter" });
  }

  try {
    // Define the path to the Python script
    const scriptPath = path.join(process.cwd(), "../back-end/image_compare_" + tier + ".py");

    console.log(`Executing Python script: ${scriptPath}`);

    // Execute the Python script
    const output = await new Promise((resolve, reject) => {
      exec(`python3 "${scriptPath}"`, (error, stdout, stderr) => {
        if (error) {
          console.error("Execution error:", stderr);
          reject(stderr);
        } else {
          console.log("Script output:", stdout);
          resolve(stdout);
        }
      });
    });

    return NextResponse.json({ success: true, message: `Tier ${tier} script executed`, output });
  } catch (error) {
    console.error("Full error:", error);
    return NextResponse.json({ success: false, error: `Script execution failed: ${error}` });
  }
}

// API route to get clusters
export async function GETClusters() {
  try {
    const baseDir = path.join(process.cwd(), "../back-end/");
    const tiers = ["t1", "t2", "t3", "t4"];
    let clusters = {};

    // Loop through each tier and fetch the files inside the directories
    for (const tier of tiers) {
      const tierPath = path.join(baseDir, `output_clusters_${tier}`);
      
      // Check if directory exists
      if (!fs.existsSync(tierPath)) {
        console.warn(`Directory not found: ${tierPath}`);
        continue;
      }

      const files = fs.readdirSync(tierPath).filter(file => file.endsWith(".txt"));
      
      // If no files are found
      if (files.length === 0) {
        console.warn(`No txt files found in: ${tierPath}`);
      }

      // Read the content of each file and add it to the clusters object
      clusters[tier] = files.map(file => {
        const content = fs.readFileSync(path.join(tierPath, file), "utf-8");
        return { filename: file, content };
      });
    }

    return NextResponse.json({ success: true, clusters });
  } catch (error) {
    console.error("Error reading clusters:", error);
    return NextResponse.json({ success: false, error: "Failed to load clusters" });
  }
}
