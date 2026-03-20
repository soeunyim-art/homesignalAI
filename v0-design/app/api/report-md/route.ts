import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET() {
  try {
    // 프로젝트 루트의 모델링_종합보고서.md 읽기
    const filePath = path.join(process.cwd(), "..", "모델링_종합보고서.md");
    const content = fs.readFileSync(filePath, "utf-8");
    return NextResponse.json({ content });
  } catch {
    return NextResponse.json({ error: "파일을 찾을 수 없습니다." }, { status: 404 });
  }
}
