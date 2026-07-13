export default function Nav({ alias }) {
  const links = [
    ["projects", "#projects"],
    ["certs", "#certifications"],
    ["experience", "#experience"],
    ["education", "#education"],
    ["labs", "#labs"],
    ["blog", "#blog"],
    ["contact", "#contact"]
  ];
  return (
    <nav className="nav">
      <div className="nav-inner">
        <a href="#top" className="logo">
          {alias}@sec<span className="tilde">:~#</span>
        </a>
        <div className="nav-links">
          {links.map(([label, href]) => (
            <a key={href} href={href}>/{label}</a>
          ))}
        </div>
        <a className="nav-cta" href="#contact">[ contact ]</a>
      </div>
    </nav>
  );
}
