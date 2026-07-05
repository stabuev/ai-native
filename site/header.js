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
     </div>`;
  document.body.insertBefore(el, document.body.firstChild);
})();
