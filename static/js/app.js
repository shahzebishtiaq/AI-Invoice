(() => {
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".primary-navigation");
  if (!toggle || !nav) return;
  const closeMenu = () => { toggle.setAttribute("aria-expanded", "false"); nav.classList.remove("is-open"); document.body.classList.remove("menu-open"); };
  toggle.addEventListener("click", () => { const open = toggle.getAttribute("aria-expanded") === "true"; toggle.setAttribute("aria-expanded", String(!open)); nav.classList.toggle("is-open", !open); document.body.classList.toggle("menu-open", !open); });
  nav.addEventListener("click", e => { if (e.target.closest("a")) closeMenu(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeMenu(); });
  window.addEventListener("resize", () => { if (window.innerWidth > 720) closeMenu(); });
})();
