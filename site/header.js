/* header.js — общий хедер/навигация. Подсвечивает активную страницу по body[data-page]. */
(function () {
  const page = document.body.getAttribute("data-page") || "";
  const B = window.__BASE__ || "";               // "" на верхних страницах, "../../" на страницах уроков
  const links = [
    ["index", "index.html", "Главная"],
    ["catalog", "catalog.html", "Каталог"],
    ["prereqs", "prereqs.html", "Требования"],
    ["glossary", "glossary.html", "Глоссарий"],
  ];
  const nav = links.map(([id, href, label]) =>
    `<a href="${B}${href}" class="${id === page ? "active" : ""}">${label}</a>`).join("");
  const el = document.createElement("header");
  el.className = "site";
  el.innerHTML =
    `<div class="container row">
       <a class="brand" href="${B}index.html">AI <span>Native</span></a>
       <nav>${nav}
         <a href="https://github.com/stabuev/ai-native" target="_blank" rel="noopener">GitHub</a>
       </nav>
       <button type="button" class="theme-toggle" aria-label="Переключить тему"></button>
     </div>`;
  document.body.insertBefore(el, document.body.firstChild);

  // переключатель темы: тёмная ↔ светлая, выбор запоминается в localStorage
  const toggle = el.querySelector(".theme-toggle");
  const isDark = () => document.documentElement.getAttribute("data-theme") === "dark"; // свет — дефолт
  const paint = () => {
    toggle.textContent = isDark() ? "☀" : "☾";
    toggle.title = isDark() ? "Светлая тема" : "Тёмная тема";
  };
  paint();
  toggle.addEventListener("click", () => {
    const next = isDark() ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) { /* приватный режим */ }
    paint();
  });
})();
