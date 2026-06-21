/* app.js — рендеринг страниц из data.js (PHASES, META, GLOSSARY) + личный прогресс. */
const REPO = "https://github.com/stabuev/ai-native";
const $ = (sel, root = document) => root.querySelector(sel);
const flat = () => PHASES.flatMap((p) => p.lessons.map((l) => ({ ...l, phase: p })));

function statusDot(s) { return `<span class="dot ${s}" title="${s === "done" ? "урок готов" : "запланирован"}"></span>`; }

/* ---------- ГЛАВНАЯ ---------- */
function renderIndex() {
  const total = META.lessons;
  const stats = [
    [META.phases, "фаз"], [META.lessons, "уроков"],
    ["~" + META.hours, "часов"], [Progress.pct(total) + "%", "ваш прогресс"],
  ];
  $("#stats").innerHTML = stats.map(([n, l]) => `<div class="stat"><div class="n">${n}</div><div class="l">${l}</div></div>`).join("");

  $("#roadmap").innerHTML =
    "<table><thead><tr><th>Фаза</th><th>Название</th><th>Уроков</th><th>Часов</th><th>Результат фазы</th></tr></thead><tbody>"
    + PHASES.map((p) => `<tr><td>${p.id}</td><td><a href="catalog.html#phase-${p.id}">${p.name}</a></td>`
      + `<td>${p.lessons.length}</td><td>~${p.hours || "—"}</td><td class="muted">${p.outcome || ""}</td></tr>`).join("")
    + "</tbody></table>";
}

/* ---------- КАТАЛОГ ---------- */
function lessonRow(l) {
  const done = Progress.isDone(l.id);
  return `<li data-q="${(l.id + " " + l.title + " " + l.motto).toLowerCase()}">
    <input type="checkbox" class="chk" data-id="${l.id}" ${done ? "checked" : ""} title="отметить пройденным">
    ${statusDot(l.status)}
    <span class="lid">${l.id}</span>
    <span class="ltitle"><a href="lesson.html?id=${l.id}">${l.title}</a>${l.motto ? `<small>${l.motto}</small>` : ""}</span>
  </li>`;
}
function phaseBlock(p) {
  const total = p.lessons.length;
  const mine = p.lessons.filter((l) => Progress.isDone(l.id)).length;
  return `<div class="phase" id="phase-${p.id}">
    <div class="head"><span class="pnum">${p.id}</span><span class="pname">${p.name}</span>
      <span class="pmeta">${total} уроков · ~${p.hours || "—"} ч · пройдено ${mine}/${total}</span></div>
    <div class="outcome">${p.outcome || ""}</div>
    <div class="container" style="padding:0 18px 6px"><div class="bar"><i style="width:${total ? mine / total * 100 : 0}%"></i></div></div>
    <ul class="lessons">${p.lessons.map(lessonRow).join("")}</ul>
  </div>`;
}
function renderCatalog() {
  const box = $("#catalog");
  box.innerHTML = PHASES.map(phaseBlock).join("");
  box.addEventListener("change", (e) => {
    if (e.target.classList.contains("chk")) {
      Progress.set(e.target.dataset.id, e.target.checked);
      renderCatalog();
      if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
    }
  });
  const search = $("#search");
  if (search) search.addEventListener("input", () => {
    const q = search.value.trim().toLowerCase();
    box.querySelectorAll(".lessons li").forEach((li) => {
      li.style.display = !q || li.dataset.q.includes(q) ? "" : "none";
    });
  });
}

/* ---------- УРОК ---------- */
function renderLesson() {
  const id = new URLSearchParams(location.search).get("id");
  const list = flat();
  const idx = list.findIndex((l) => l.id === id);
  const art = $("#lesson");
  if (idx < 0) { art.innerHTML = "<p>Урок не найден. <a href='catalog.html'>В каталог →</a></p>"; return; }
  const l = list[idx];
  document.title = `${l.id} ${l.title} — AI Native`;
  art.innerHTML = l.html;

  const done = Progress.isDone(l.id);
  $("#lessonbar").innerHTML =
    `<span class="badge">Урок <b>${idx + 1}</b> из ${list.length}</span>
     <span class="badge">Фаза <b>${l.phase.id}</b> · ${l.phase.name}</span>
     ${l.hours ? `<span class="badge">~${l.hours} ч</span>` : ""}
     <button class="btn ${done ? "ghost" : ""}" id="markBtn">${done ? "✓ Пройдено" : "Отметить пройденным"}</button>
     ${l.dir ? `<a class="badge" href="${REPO}/tree/main/${l.dir}" target="_blank" rel="noopener">Исходник на GitHub ↗</a>` : ""}`;
  $("#markBtn").addEventListener("click", () => {
    Progress.toggle(l.id);
    renderLesson();
  });

  const prev = list[idx - 1], next = list[idx + 1];
  $("#prevnext").innerHTML =
    (prev ? `<a href="lesson.html?id=${prev.id}"><small>← ${prev.id}</small>${prev.title}</a>` : "<span></span>")
    + (next ? `<a href="lesson.html?id=${next.id}" style="text-align:right"><small>${next.id} →</small>${next.title}</a>` : "<span></span>");
}

/* ---------- ГЛОССАРИЙ ---------- */
function renderGlossary() {
  $("#glossary").innerHTML = GLOSSARY.map((g) =>
    `<div class="term"><h3>${g.term}</h3><div class="says">${g.says}</div><div class="muted">${g.means}</div></div>`).join("");
}

document.addEventListener("DOMContentLoaded", () => {
  const page = document.body.getAttribute("data-page");
  ({ index: renderIndex, catalog: renderCatalog, lesson: renderLesson, glossary: renderGlossary }[page] || (() => {}))();
});
