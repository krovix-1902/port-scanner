import { NextResponse } from "next/server";
import { getData, writeData, SECTIONS } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET(_req, { params }) {
  const { section } = params;
  if (!SECTIONS.includes(section)) {
    return NextResponse.json({ error: "unknown section" }, { status: 404 });
  }
  return NextResponse.json(getData(section));
}

export async function PUT(req, { params }) {
  const { section } = params;
  if (!SECTIONS.includes(section)) {
    return NextResponse.json({ error: "unknown section" }, { status: 404 });
  }
  try {
    const body = await req.json();
    writeData(section, body);
    return NextResponse.json({ ok: true });
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 400 });
  }
}
