import { NextRequest, NextResponse } from "next/server";
import path from "path";
import fs from "fs/promises";

async function directoryExists(dirPath: string): Promise<boolean> {
  try {
    await fs.access(dirPath);
    return true;
  } catch {
    return false;
  }
}

export async function GET(req: NextRequest): Promise<NextResponse> {
  try {
    const clusterData: Record<string, { filename: string; content: string }[]> = {};
    const baseDir = process.env.BACKEND_DIR || path.join(process.cwd(), "../back-end");
    let successCount = 0;

    for (let tier = 1; tier <= 4; tier++) {
      const dirPath = path.join(baseDir, `output_clusters_t${tier}`);

      if (await directoryExists(dirPath)) {
        try {
          const files = await fs.readdir(dirPath);
          const fileReadPromises = files
            .filter((file) => file.endsWith(".txt"))
            .map(async (file) => {
              const filePath = path.join(dirPath, file);
              const content = await fs.readFile(filePath, "utf-8");
              return { filename: file, content };
            });

          const tierClusters = await Promise.all(fileReadPromises);
          clusterData[`Tier ${tier}`] = tierClusters;
          successCount++;
        } catch (error) {
          console.warn(`Error reading cluster files for Tier ${tier}:`, error);
        }
      } else {
        console.warn(`Directory not found: ${dirPath}`);
      }
    }

    const totalClusters = Object.values(clusterData).reduce((acc, tierClusters) => acc + tierClusters.length, 0);
    return NextResponse.json({ success: true, clusters: clusterData, successCount, totalClusters });
  } catch (error) {
    console.error("Failed to fetch clusters:", error);
    return NextResponse.json({ success: false, error: "Failed to fetch clusters" });
  }
}