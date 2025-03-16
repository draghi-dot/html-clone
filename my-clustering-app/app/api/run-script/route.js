// api/run-script/route.js
import { exec } from "child_process";
import path from "path";
import { NextResponse } from "next/server";

export async function GET(req) {
  const { searchParams } = new URL(req.url);
  const tier = searchParams.get("tier");

  // Validate tier
  if (!tier || !["1", "2", "3", "4"].includes(tier)) {
    return NextResponse.json({ success: false, error: "Invalid tier parameter" });
  }

  try {
    const scriptPath = path.join(process.cwd(), `../back-end/image_compare_${tier}.py`);

    console.log(`Executing script: ${scriptPath}`);

    const output = await new Promise((resolve, reject) => {
      exec(`python3 "${scriptPath}"`, (error, stdout, stderr) => {
        if (error) {
          reject(stderr);
        } else {
          resolve(stdout);
        }
      });
    });

    return NextResponse.json({ success: true, message: `Tier ${tier} script executed`, output });
  } catch (error) {
    console.error("Full error:", error);
    return NextResponse.json({ success: false, error: `Script execution failed: ${error.message}` });
  }
}
