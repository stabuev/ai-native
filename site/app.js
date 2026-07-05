/* app.js — рендеринг страниц из data.js (PHASES, META, GLOSSARY) + личный прогресс. */
const $ = (sel, root = document) => root.querySelector(sel);
const BASE = () => window.__BASE__ || "";          // "" на верхних страницах, "../../" на страницах уроков
const lessonURL = (l) => `${BASE()}lessons/${l.slug}/`;   // чистый URL урока

/* кнопка «Копировать» на встроенных блоках кода (делегирование, переживает ре-рендер) */
document.addEventListener("click", (e) => {
  const btn = e.target.closest(".copy-btn");
  if (!btn) return;
  e.preventDefault();                      // не сворачивать <details> при клике в summary
  const code = btn.closest(".filebox")?.querySelector("pre code");
  if (!code || !navigator.clipboard) return;
  flashCopy(btn, code.textContent, "Скопировано ✓");
});

/* кнопка «Скопировать промпт для ИИ» — собирает промпт из задания (BUILD IT) + тестов */
document.addEventListener("click", (e) => {
  const btn = e.target.closest(".ai-prompt-btn");
  if (!btn || !navigator.clipboard) return;
  e.preventDefault();
  const bi = [...document.querySelectorAll("#lesson h2")].find((h) => h.textContent.trim() === "BUILD IT");
  let task = "";
  if (bi) {
    const buf = [];
    for (let n = bi.nextElementSibling; n && n.tagName !== "H2"; n = n.nextElementSibling) buf.push(n.innerText);
    task = buf.join("\n").trim();
  }
  const tests = [...document.querySelectorAll('.lesson-files .filebox[data-test="1"] pre code')]
    .map((c) => c.textContent).join("\n\n");
  const prompt =
    "Реши учебное упражнение. Напиши код на Python (только стандартная библиотека), который проходит "
    + "приведённые тесты pytest. Тесты не меняй. Верни только код файла, без пояснений.\n\n"
    + "# Задание\n" + task + "\n\n# Тесты (pytest)\n" + tests;
  flashCopy(btn, prompt, "Промпт скопирован ✓");
});

function flashCopy(btn, text, okLabel) {
  navigator.clipboard.writeText(text).then(() => {
    const old = btn.textContent;
    btn.textContent = okLabel; btn.classList.add("copied");
    setTimeout(() => { btn.textContent = old; btn.classList.remove("copied"); }, 1600);
  });
}
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
    <span class="ltitle"><a href="${lessonURL(l)}">${l.title}</a>${l.motto ? `<small>${l.motto}</small>` : ""}</span>
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
  const id = document.body.dataset.lessonId || new URLSearchParams(location.search).get("id");
  const list = flat();
  const idx = list.findIndex((l) => l.id === id);
  const art = $("#lesson");
  if (idx < 0) { art.innerHTML = `<p>Урок не найден. <a href='${BASE()}catalog.html'>В каталог →</a></p>`; return; }
  const l = list[idx];
  document.title = `${l.id} ${l.title} — AI Native`;
  if (art.dataset.ssr !== "1") art.innerHTML = l.html;   // на статической странице контент уже вшит (SSR) — не перерисовываем

  const mount = art.querySelector(".quiz-section[data-lesson]");
  if (mount && l.quiz && l.quiz.questions) renderQuiz(mount, l.quiz);

  const done = Progress.isDone(l.id);
  $("#lessonbar").innerHTML =
    `<span class="badge">Урок <b>${idx + 1}</b> из ${list.length}</span>
     <span class="badge">Фаза <b>${l.phase.id}</b> · ${l.phase.name}</span>
     ${l.hours ? `<span class="badge">~${l.hours} ч</span>` : ""}
     <button class="btn ${done ? "ghost" : ""}" id="markBtn">${done ? "✓ Пройдено" : "Отметить пройденным"}</button>
     ${l.html && l.html.includes('id="lesson-files"') ? `<a class="badge" href="#lesson-files">Код и артефакт ↓</a>` : ""}`;
  $("#markBtn").addEventListener("click", () => {
    Progress.toggle(l.id);
    renderLesson();
  });

  const prev = list[idx - 1], next = list[idx + 1];
  $("#prevnext").innerHTML =
    (prev ? `<a href="${lessonURL(prev)}"><small>← ${prev.id}</small>${prev.title}</a>` : "<span></span>")
    + (next ? `<a href="${lessonURL(next)}" style="text-align:right"><small>${next.id} →</small>${next.title}</a>` : "<span></span>");
}

/* ---------- КВИЗ УРОКА (монтируется в тег {{quiz}}) ---------- */
function renderQuiz(mount, quiz) {
  const qs = quiz.questions || [];
  mount.innerHTML =
    `<div class="quiz-head">🧠 Мини-квиз · ${qs.length} вопрос(ов)</div>` +
    qs.map((q, qi) =>
      `<div class="quiz-q" data-correct="${q.correct}">
         <div class="quiz-qt">${qi + 1}. ${q.question}</div>
         <div class="quiz-opts">` +
        q.options.map((o, oi) => `<button class="quiz-opt" data-oi="${oi}">${o}</button>`).join("") +
        `</div>
         <div class="quiz-exp" hidden>${q.explanation || ""}</div>
       </div>`).join("") +
    `<div class="quiz-score" hidden></div>`;

  let answered = 0, correct = 0;
  const scoreEl = mount.querySelector(".quiz-score");
  mount.querySelectorAll(".quiz-q").forEach((qel) => {
    const corr = +qel.dataset.correct;
    qel.querySelectorAll(".quiz-opt").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (qel.classList.contains("done")) return;        // отвечаем один раз
        qel.classList.add("done");
        const oi = +btn.dataset.oi;
        qel.querySelectorAll(".quiz-opt").forEach((b, i) => {
          b.disabled = true;
          if (i === corr) b.classList.add("ok");
        });
        if (oi !== corr) btn.classList.add("bad"); else correct++;
        qel.querySelector(".quiz-exp").hidden = false;
        answered++;
        if (answered === qs.length) {
          const pct = Math.round(correct / qs.length * 100);
          scoreEl.hidden = false;
          scoreEl.textContent =
            `Результат: ${correct} из ${qs.length} (${pct}%) — ${pct >= 80 ? "сдано ✓" : "стоит повторить урок"}`;
        }
      });
    });
  });
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
