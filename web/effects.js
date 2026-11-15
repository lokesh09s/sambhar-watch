// Page effects only: reveal-on-scroll, menu highlight and scroll progress. No data logic (that is app.js).
(function () {
  const root = document.documentElement;
  root.classList.add("js");   // without this class nothing is hidden, so the page still works if this file fails

  // Fade sections and cards in as they enter the screen.
  const targets = document.querySelectorAll("main > section, .band, .card");
  targets.forEach(el => el.classList.add("reveal"));
  const revealer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("in");
        revealer.unobserve(entry.target);
      }
    });
  }, { rootMargin: "0px 0px -8% 0px" });   // as soon as any part is 8% up the screen, however tall the section
  targets.forEach(el => revealer.observe(el));

  // Highlight the menu link of the section on screen.
  const links = new Map();
  document.querySelectorAll(".nav-links a").forEach(a => links.set(a.getAttribute("href").slice(1), a));
  const spy = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        links.forEach(a => a.classList.remove("current"));
        links.get(entry.target.id).classList.add("current");
      }
    });
  }, { rootMargin: "-45% 0px -50% 0px" });
  links.forEach((a, id) => { const el = document.getElementById(id); if (el) spy.observe(el); });

  // Thin progress bar and menu shadow while scrolling.
  const bar = document.getElementById("progress");
  const nav = document.querySelector(".nav");
  const shot = document.getElementById("shot");
  function onScroll() {
    const scrollable = root.scrollHeight - window.innerHeight;
    bar.style.transform = "scaleX(" + (scrollable > 0 ? window.scrollY / scrollable : 0) + ")";
    nav.classList.toggle("scrolled", window.scrollY > 8);
    // The opening image grows from 86% to full width over the first 40% of a screen of scrolling.
    shot.style.setProperty("--grow", Math.min(1, window.scrollY / (0.4 * window.innerHeight)));
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
})();
