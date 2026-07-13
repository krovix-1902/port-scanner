"use client";
import { useEffect, useState } from "react";

export default function Scanner({ rows, host, prompt }) {
  const CMD = "nmap -sV --open " + host;
  const [typed, setTyped] = useState(0);
  const [lines, setLines] = useState(0);
  const done = typed >= CMD.length;

  useEffect(() => {
    if (typed < CMD.length) {
      const t = setTimeout(() => setTyped((v) => v + 1), 38);
      return () => clearTimeout(t);
    }
    if (lines <= rows.length + 2) {
      const t = setTimeout(() => setLines((v) => v + 1), lines === 0 ? 500 : 140);
      return () => clearTimeout(t);
    }
  }, [typed, lines, rows.length, CMD.length]);

  return (
    <div className="scanbox" aria-label="Site navigation, styled as a port scan">
      <div className="scanhead">
        <span className="dot r" /><span className="dot y" /><span className="dot g" />
        <span className="scantitle">recon — zsh</span>
      </div>
      <div className="scanbody">
        <span className="scanline">
          <span className="prompt">{prompt} </span>
          {CMD.slice(0, typed)}
          {!done && <span className="cursor" />}
        </span>
        {done && lines >= 1 && (
          <span className="scanline muted">Recon initiated — 1 host up, {rows.length} services exposed</span>
        )}
        {done && lines >= 2 && (
          <span className="scanline head"><span>PORT</span><span>STATE</span><span>SERVICE</span></span>
        )}
        {done && rows.slice(0, Math.max(0, lines - 2)).map((r) => (
          <a key={r.href} className="scanline portrow" href={r.href}>
            <span className="port">{r.port}</span>
            <span className="state">open</span>
            <span className="svc">{r.service}</span>
          </a>
        ))}
        {done && lines > rows.length + 2 && (
          <span className="scanline"><span className="prompt">{prompt} </span><span className="cursor" /></span>
        )}
      </div>
    </div>
  );
}
