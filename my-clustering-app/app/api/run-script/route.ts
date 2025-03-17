import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import path from "path";
import fs from "fs";

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const tier = url.searchParams.get("tier")?.toString();

    if (!tier || !["1", "2", "3", "4"].includes(tier)) {
      return NextResponse.json({ success: false, error: "Invalid tier parameter" }, { status: 400 });
    }

    const baseDir = process.env.BACKEND_DIR || path.join(process.cwd(), "../back-end");
    const scriptPath = path.join(baseDir, `image_compare_${tier}.py`);

    if (!fs.existsSync(scriptPath)) {
      console.error(`Script not found: ${scriptPath}`);
      return NextResponse.json({ success: false, error: `Script for tier ${tier} not found` }, { status: 404 });
    }

    console.log(`Executing script: ${scriptPath}`); 

    return new Promise((resolve) => {
      const childProcess = exec(`python "${scriptPath}"`, (error, stdout, stderr) => {
        if (error) {
          console.error(`Execution error: ${stderr}`); 
          return resolve(NextResponse.json({ success: false, error: stderr || "Script execution failed" }, { status: 500 }));
        }
        console.log(`Script output: ${stdout}`); 
        resolve(NextResponse.json({ success: true, message: `Tier ${tier} script executed`, output: stdout }));
      });
    });
  } catch (error) {
    console.error("Server error:", error); 
    return NextResponse.json({ success: false, error: "Server error" }, { status: 500 });
  }
}
