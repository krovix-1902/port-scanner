import fs from "fs";
import path from "path";

const DATA_DIR = path.join(process.cwd(), "data");

export const SECTIONS = [
  "profile",
  "projects",
  "certifications",
  "education",
  "experience",
  "hobbies",
  "labs",
  "blogs"
];

export function getData(section) {
  if (!SECTIONS.includes(section)) throw new Error("Unknown section: " + section);
  const file = path.join(DATA_DIR, section + ".json");
  return JSON.parse(fs.readFileSync(file, "utf-8"));
}

export function writeData(section, payload) {
  if (!SECTIONS.includes(section)) throw new Error("Unknown section: " + section);
  const file = path.join(DATA_DIR, section + ".json");
  fs.writeFileSync(file, JSON.stringify(payload, null, 2));
}
