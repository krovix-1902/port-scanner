import { getData } from "@/lib/data";
import Nav from "@/components/Nav";
import Scanner from "@/components/Scanner";
import Reveal from "@/components/Reveal";

export const dynamic = "force-dynamic";

function SectionHead({ num, title }) {
  return (
    <div className="sec-head">
      <span className="sec-num">FINDING {num}</span>
      <h2>{title}</h2>
      <span className="sec-rule" />
    </div>
  );
}

export default function Home() {
  const profile = getData("profile");
  const projects = getData("projects");
  const certifications = getData("certifications");
  const education = getData("education");
  const experience = getData("experience");
  const hobbies = getData("hobbies");
  const labs = getData("labs");
  const blogs = getData("blogs");

  const prompt = profile.handle + ":~$";

  const scanRows = [
    { port: "22/tcp", service: "projects", href: "#projects" },
    { port: "80/tcp", service: "certifications", href: "#certifications" },
    { port: "443/tcp", service: "experience", href: "#experience" },
    { port: "3306/tcp", service: "education", href: "#education" },
    { port: "4444/tcp", service: "labs", href: "#labs" },
    { port: "8080/tcp", service: "blog", href: "#blog" },
    { port: "1337/tcp", service: "hobbies", href: "#hobbies" },
    { port: "31337/tcp", service: "contact", href: "#contact" }
  ];

  const hasLatest = blogs.latest && blogs.latest.title;

  return (
    <>
      <Nav alias={profile.alias} />
      <main className="container" id="top">
        <header className="hero">
          <p className="hero-kicker">// {profile.role} — aka {profile.alias} — {profile.location}</p>
          <h1>
            Hi, I&apos;m <span className="accent">{profile.name}</span>.
            <br />Online, I&apos;m <span className="accent">{profile.alias}</span>.
          </h1>
          <p className="hero-tagline">{profile.tagline}</p>
          <Scanner rows={scanRows} host={profile.host} prompt={prompt} />
        </header>

        <section className="sec" id="projects">
          <Reveal>
            <SectionHead num="01" title="Projects" />
            <div className="cards">
              {projects.map((p, i) => (
                <article className="card" key={p.title}>
                  <div className="card-top">
                    <h3>{p.title}</h3>
                    <span className={"sev sev-" + p.severity}>{p.severity}</span>
                  </div>
                  <p className="proj-why"><b>Why:</b> {p.why}</p>
                  <p className="proj-solves">{p.solves}</p>
                  <div className="tags">
                    {p.tags.map((t) => <span className="tag" key={t}>{t}</span>)}
                  </div>
                  <div className="card-top" style={{ marginTop: "auto" }}>
                    <span className="proj-idx">#{String(i + 1).padStart(2, "0")} / {projects.length}</span>
                    <span className={"pill " + (p.status === "in progress" ? "pill-progress" : "pill-obtained")}>{p.status}</span>
                  </div>
                </article>
              ))}
            </div>
          </Reveal>
        </section>

        <section className="sec" id="certifications">
          <Reveal>
            <SectionHead num="02" title="Certifications" />
            <div className="certs-grid">
              {certifications.map((c) => {
                const card = (
                  <>
                    <div className="cert-logo">
                      <img src={c.logo} alt={c.name + " badge"} loading="lazy" />
                    </div>
                    <h3>{c.name}</h3>
                    <div className="cert-issuer">{c.issuer}</div>
                    <div className="cert-meta">
                      <span className={"pill " + (c.status === "obtained" ? "pill-obtained" : "pill-progress")}>{c.status}</span>
                    </div>
                  </>
                );
                return c.link
                  ? <a className="certcard" key={c.name} href={c.link} target="_blank" rel="noreferrer">{card}</a>
                  : <article className="certcard" key={c.name}>{card}</article>;
              })}
            </div>
          </Reveal>
        </section>

        <section className="sec" id="experience">
          <Reveal>
            <SectionHead num="03" title="Work experience" />
            <div className="tl">
              {experience.map((e) => (
                <div className="tl-item" key={e.role + e.period}>
                  <span className="tl-period">{e.period}</span>
                  <h3>{e.role}</h3>
                  <div className="tl-org">{e.company}</div>
                  <p>{e.detail}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </section>

        <section className="sec" id="education">
          <Reveal>
            <SectionHead num="04" title="Education" />
            <div className="tl">
              {education.map((e) => (
                <div className="tl-item" key={e.degree}>
                  <span className="tl-period">{e.period}</span>
                  <h3>{e.degree}</h3>
                  <div className="tl-org">{e.school}</div>
                  <p>{e.detail}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </section>

        <section className="sec" id="labs">
          <Reveal>
            <SectionHead num="05" title="Live labs" />
            <div className="labs-grid">
              {labs.map((l) => (
                <article className="labcard" key={l.id}>
                  <div className="lab-head">
                    <h3>{l.platform}</h3>
                    <span className="lab-banner">{l.rank}</span>
                  </div>
                  <div style={{ padding: "12px 18px 0" }}>
                    <div style={{ fontSize: "11px", color: "var(--faint)", fontFamily: "var(--mono)", marginBottom: "5px" }}>{l.progressLabel}</div>
                    <div style={{ height: "5px", background: "var(--line-soft)", borderRadius: "3px", overflow: "hidden" }}>
                      <div style={{ width: l.progressPct + "%", height: "100%", background: "var(--accent)" }} />
                    </div>
                  </div>
                  <div className="lab-stats">
                    {l.stats.map((s) => (
                      <div className="lab-stat" key={s.label}>
                        <div className="v">{s.value}</div>
                        <div className="l">{s.label}</div>
                      </div>
                    ))}
                  </div>
                  <a className="lab-connect" href={l.url} target="_blank" rel="noreferrer">
                    <span>open profile ▸</span>
                    <span className="lab-user">{l.username}</span>
                  </a>
                </article>
              ))}
            </div>
          </Reveal>
        </section>

        <section className="sec" id="blog">
          <Reveal>
            <SectionHead num="06" title="Blog" />
            <div className="blog-feature">
              {hasLatest ? (
                <a className="blog-card" href={blogs.latest.url} target="_blank" rel="noreferrer">
                  <span className="blog-badge">LATEST POST</span>
                  <h3>{blogs.latest.title}</h3>
                  {blogs.latest.date && <div className="row-date" style={{ marginBottom: "8px" }}>{blogs.latest.date}</div>}
                  <p>{blogs.latest.excerpt}</p>
                  <span className="read">read more ▸</span>
                </a>
              ) : (
                <div className="blog-soon">
                  <p><span className="prompt">{prompt} </span>curl {blogs.blogUrl}/latest</p>
                  <p className="muted">No posts published yet — the feed is empty.</p>
                  <p>First writeups are being compiled: CTF investigations, detection-engineering notes, and lessons from the homelab. The newest post will appear right here and link straight to the blog.</p>
                </div>
              )}
              <div>
                <a className="blog-visit" href={blogs.blogUrl} target="_blank" rel="noreferrer">
                  <span>visit the full blog</span><span>↗</span>
                </a>
              </div>
            </div>
          </Reveal>
        </section>

        <section className="sec" id="hobbies">
          <Reveal>
            <SectionHead num="07" title="Off the clock" />
            <div className="chips">
              {hobbies.map((h) => (
                <div className="chip" key={h.name}>
                  <div className="n">{h.name}</div>
                  <div className="d">{h.note}</div>
                </div>
              ))}
            </div>
          </Reveal>
        </section>

        <section className="sec" id="contact">
          <Reveal>
            <SectionHead num="08" title="Contact" />
            <div className="contact-grid">
              <div className="contact-card">
                <div><span className="prompt">{prompt} </span>cat contact.txt</div>
                <div><span className="k">name&nbsp;&nbsp;&nbsp;→ </span>{profile.name} <span className="k">(aka {profile.alias})</span></div>
                <div><span className="k">mail&nbsp;&nbsp;&nbsp;→ </span><a href={"mailto:" + profile.email}>{profile.email}</a></div>
                <div><span className="k">tel&nbsp;&nbsp;&nbsp;&nbsp;→ </span><a href={"tel:" + profile.phone.replace(/\s/g, "")}>{profile.phone}</a></div>
                <div><span className="k">loc&nbsp;&nbsp;&nbsp;&nbsp;→ </span>{profile.location}</div>
                <div><span className="prompt">{prompt} </span><span className="cursor" /></div>
              </div>
              <div className="contact-actions">
                {profile.socials.map((s) => (
                  <a className="contact-btn" key={s.label} href={s.url} target="_blank" rel="noreferrer">
                    <span className="cl">{s.label}</span>
                    <span className="cv">↗</span>
                  </a>
                ))}
              </div>
            </div>
          </Reveal>
        </section>

        <footer className="footer">
          <p className="footer-eof"><span className="accent">EOF</span> — end of report</p>
          <p className="footer-note">© {new Date().getFullYear()} {profile.name} · aka {profile.alias} · built with Next.js · content served from ./data/*.json</p>
        </footer>
      </main>
    </>
  );
}
