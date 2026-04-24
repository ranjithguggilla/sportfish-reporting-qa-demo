const API_BASE = "";
const VALID_SPECIES = ["RED_SNAPPER", "COBIA", "SHARK", "TARPON", "FLOUNDER", "SNOOK"];

function syncRoleFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const urlRole = params.get("role");
  if (urlRole && ["angler", "analyst"].includes(urlRole.toLowerCase())) {
    localStorage.setItem("portalRole", urlRole.toLowerCase());
  }
  if (!localStorage.getItem("portalRole")) {
    localStorage.setItem("portalRole", "angler");
  }
}

function getRole() {
  return localStorage.getItem("portalRole") || "angler";
}

async function getJson(url, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    "X-Role": getRole(),
    ...(options.headers || {}),
  };
  const res = await fetch(`${API_BASE}${url}`, {
    headers,
    ...options,
  });
  if (!res.ok) {
    let message = `Request failed: ${res.status}`;
    try {
      const payload = await res.json();
      message = payload.detail || payload.message || message;
    } catch (_) {
      const text = await res.text();
      if (text) message = text;
    }
    throw new Error(message);
  }
  return await res.json();
}

function nav() {
  const role = getRole();
  const analystSuffix = role === "analyst" ? "?role=analyst" : "";
  return `
    <header>
      <h2>Reporting and Tagging Intelligence Portal</h2>
      <nav>
        <a href="/">Home</a>
        <a href="/submit-trip">Submit Trip</a>
        <a href="/my-contributions">My Contributions</a>
        <a href="/analyst/queue${analystSuffix}">Analyst Queue</a>
        <a href="/analyst/exports${analystSuffix}">Analyst Exports</a>
        <label style="margin-left:12px">Role</label>
        <select id="roleSelect">
          <option value="angler" ${role === "angler" ? "selected" : ""}>angler</option>
          <option value="analyst" ${role === "analyst" ? "selected" : ""}>analyst</option>
        </select>
      </nav>
    </header>
  `;
}

function setActiveNavLink() {
  const path = window.location.pathname;
  const links = document.querySelectorAll("header nav a");
  links.forEach((link) => {
    const href = link.getAttribute("href") || "";
    const hrefPath = href.split("?")[0];
    if (
      (hrefPath === "/" && path === "/") ||
      (hrefPath !== "/" && path.startsWith(hrefPath))
    ) {
      link.classList.add("nav-active");
    } else {
      link.classList.remove("nav-active");
    }
  });
}

function addStaggerReveal() {
  const candidates = document.querySelectorAll("main > *");
  candidates.forEach((node, index) => {
    node.classList.add("reveal-item");
    node.style.setProperty("--reveal-delay", `${Math.min(index * 70, 500)}ms`);
  });
  window.requestAnimationFrame(() => {
    candidates.forEach((node) => node.classList.add("reveal-visible"));
  });
}

function animateNumber(el, end, duration = 700) {
  const target = Number(end) || 0;
  const start = 0;
  const startTime = performance.now();

  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = Math.round(start + (target - start) * eased);
    el.textContent = String(value);
    if (progress < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

function bootNav() {
  syncRoleFromUrl();
  const navNode = document.getElementById("nav");
  if (!navNode) return;
  navNode.innerHTML = nav();
  setActiveNavLink();
  const roleSelect = document.getElementById("roleSelect");
  if (roleSelect) {
    roleSelect.onchange = () => {
      localStorage.setItem("portalRole", roleSelect.value);
      window.location.search = roleSelect.value === "analyst" ? "?role=analyst" : "";
    };
  }
  addStaggerReveal();
}

function parseSpeciesList(text) {
  const list = text
    .split(",")
    .map((s) => s.trim().toUpperCase())
    .filter(Boolean);
  const invalid = list.filter((s) => !VALID_SPECIES.includes(s));
  return { list, invalid };
}

window.portal = {
  getJson,
  nav,
  bootNav,
  getRole,
  parseSpeciesList,
  VALID_SPECIES,
  animateNumber,
};
