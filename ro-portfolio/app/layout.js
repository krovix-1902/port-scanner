import "./globals.css";

export const metadata = {
  title: "Ro — Cybersecurity Portfolio",
  description: "Cybersecurity student. Projects, certifications, CTF labs, and writeups."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
