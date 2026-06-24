#!/usr/bin/env node
/* build.js — генератор статичного сайта курса AI Native.
 *
 * Источник правды: PROGRESS.md (фазы, уроки, статус), phases/<...>/docs/ru.md
 * (контент уроков), README.md (часы и результат фазы), glossary/terms.md (глоссарий).
 * Рендерит каждый урок из Markdown в HTML и пишет site/data.js (PHASES, GLOSSARY, META).
 * Без зависимостей.
 *
 * Запуск:  node site/build.js
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const PHASES_DIR = path.join(ROOT, "phases");

// ---------- мини-рендер Markdown -> HTML ----------
function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// текстовые файлы, которые встраиваем в страницу урока (Build It / Ship It)
const TEXT_EXT = new Set(["py", "md", "txt", "json", "toml", "yaml", "yml", "cfg", "ini", "sh", "js", "ts", "csv", "mk"]);
function isTextFile(p) {
  const b = path.basename(p).toLowerCase();
  if (TEXT_EXT.has(path.extname(p).slice(1).toLowerCase())) return true;
  if (b.startsWith(".env")) return true;
  return ["dockerfile", "makefile", "requirements.txt", ".gitignore"].includes(b);
}
function slugify(s) {
  return "f-" + s.replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-+|-+$/g, "").toLowerCase();
}
function walkText(absDir, acc) {
  for (const e of fs.readdirSync(absDir, { withFileTypes: true })) {
    if (["__pycache__", ".git", "node_modules"].includes(e.name)) continue;
    const p = path.join(absDir, e.name);
    if (e.isDirectory()) walkText(p, acc);
    else if (isTextFile(p)) acc.push(p);
  }
  return acc;
}

// контекст текущего урока для inline(): переписывание относительных ссылок + сбор файлов
let CTX = null;

function inline(text) {
  // 1. защищаем код-спаны плейсхолдерами, чтобы ссылки [`code`](url) не ломались по backtick
  const codes = [];
  let s = text.replace(/`([^`]+)`/g, (m, c) => {
    codes.push("<code>" + esc(c) + "</code>");
    return "" + (codes.length - 1) + "";
  });
  s = esc(s);
  // 2. ссылки; относительные пути переписываем через CTX (на якоря встроенных файлов / site-страницы)
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (m, t, u) => {
    let href = u, blank = /^https?:/i.test(u);
    if (CTX) { const r = CTX.rewrite(u); href = r.href; blank = r.blank; }
    const attr = blank ? ' target="_blank" rel="noopener"' : "";
    return `<a href="${href}"${attr}>${t}</a>`;
  });
  // 3. жирный
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  // 4. восстанавливаем код-спаны
  return s.replace(/(\d+)/g, (m, i) => codes[+i]);
}
function splitRow(line) {
  const cells = line.split("|").map((s) => s.trim());
  if (cells.length && cells[0] === "") cells.shift();
  if (cells.length && cells[cells.length - 1] === "") cells.pop();
  return cells;
}
function mdToHtml(md) {
  const lines = md.split("\n").filter((l) => !/^\s*<!--.*-->\s*$/.test(l));
  let html = "", i = 0;
  const stop = (l) => /^\s*$/.test(l) || l.startsWith("#") || l.startsWith("```")
    || l.startsWith(">") || /^\s*[-*]\s+/.test(l) || /^\s*\d+\.\s+/.test(l) || /^---+\s*$/.test(l);
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith("```")) {
      const buf = []; i++;
      while (i < lines.length && !lines[i].startsWith("```")) { buf.push(lines[i]); i++; }
      i++;
      html += "<pre><code>" + esc(buf.join("\n")) + "</code></pre>"; continue;
    }
    if (/^\s*$/.test(line)) { i++; continue; }
    if (line.includes("|") && i + 1 < lines.length && /-/.test(lines[i + 1])
        && /^\s*\|?[\s:|-]+\|?\s*$/.test(lines[i + 1])) {
      const header = splitRow(line); i += 2; const rows = [];
      while (i < lines.length && lines[i].includes("|") && lines[i].trim() !== "") {
        rows.push(splitRow(lines[i])); i++;
      }
      html += "<table><thead><tr>" + header.map((c) => "<th>" + inline(c) + "</th>").join("")
        + "</tr></thead><tbody>"
        + rows.map((r) => "<tr>" + r.map((c) => "<td>" + inline(c) + "</td>").join("") + "</tr>").join("")
        + "</tbody></table>"; continue;
    }
    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) { const lvl = h[1].length; html += `<h${lvl}>${inline(h[2])}</h${lvl}>`; i++; continue; }
    if (/^---+\s*$/.test(line)) { html += "<hr>"; i++; continue; }
    if (line.startsWith(">")) {
      const buf = [];
      while (i < lines.length && lines[i].startsWith(">")) { buf.push(lines[i].replace(/^>\s?/, "")); i++; }
      html += "<blockquote>" + inline(buf.join(" ")) + "</blockquote>"; continue;
    }
    if (/^\s*[-*]\s+/.test(line)) {
      const buf = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) { buf.push(lines[i].replace(/^\s*[-*]\s+/, "")); i++; }
      html += "<ul>" + buf.map((x) => "<li>" + inline(x) + "</li>").join("") + "</ul>"; continue;
    }
    if (/^\s*\d+\.\s+/.test(line)) {
      const buf = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) { buf.push(lines[i].replace(/^\s*\d+\.\s+/, "")); i++; }
      html += "<ol>" + buf.map((x) => "<li>" + inline(x) + "</li>").join("") + "</ol>"; continue;
    }
    const buf = [line]; i++;
    while (i < lines.length && !stop(lines[i])) { buf.push(lines[i]); i++; }
    html += "<p>" + inline(buf.join(" ")) + "</p>";
  }
  return html;
}

// ---------- индекс уроков: id -> {dir, md} ----------
function findLessons() {
  const map = {};
  for (const phase of fs.readdirSync(PHASES_DIR)) {
    const pdir = path.join(PHASES_DIR, phase);
    if (!fs.statSync(pdir).isDirectory()) continue;
    for (const lesson of fs.readdirSync(pdir)) {
      const doc = path.join(pdir, lesson, "docs", "ru.md");
      if (!fs.existsSync(doc)) continue;
      const md = fs.readFileSync(doc, "utf8");
      const m = md.match(/^#\s+Урок\s+([\d.]+)\s*·\s*(.+)$/m);
      if (m) {
        let quiz = null;
        const qp = path.join(pdir, lesson, "quiz.json");
        if (fs.existsSync(qp)) {
          try { quiz = JSON.parse(fs.readFileSync(qp, "utf8")); } catch (e) { /* invalid quiz.json */ }
        }
        map[m[1]] = { dir: `phases/${phase}/${lesson}`, md, title: m[2].trim(), quiz };
      }
    }
  }
  return map;
}

// ---------- метаданные фаз из README (часы, результат) ----------
function readmePhaseMeta() {
  const md = fs.readFileSync(path.join(ROOT, "README.md"), "utf8");
  const meta = {};
  const re = /^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|/gm;
  let m;
  while ((m = re.exec(md))) meta[m[1]] = { hours: +m[3], outcome: m[4].trim() };
  return meta;
}

function lessonMeta(md) {
  const motto = (md.match(/>\s*\*\*MOTTO\.\*\*\s*(.+)/) || [])[1] || "";
  const hours = (md.match(/\*\*Часы:\*\*\s*~?(\d+)/) || [])[1] || "";
  return { motto: motto.replace(/_/g, "").trim(), hours: hours ? +hours : null };
}

// ---------- глоссарий из glossary/terms.md ----------
function readGlossary() {
  const p = path.join(ROOT, "glossary", "terms.md");
  if (!fs.existsSync(p)) return [];
  const blocks = fs.readFileSync(p, "utf8").split(/^##\s+/m).slice(1);
  return blocks.map((b) => {
    const lines = b.split("\n");
    const term = lines[0].trim();
    let says = ""; const means = [];
    for (const l of lines.slice(1)) {
      if (/^>\s+/.test(l)) says = l.replace(/^>\s+/, "").trim();
      else if (l.trim() !== "") means.push(l.trim());
    }
    return { term, says, means: means.join(" ") };
  }).filter((t) => t.term);
}

// ---------- встраивание кода и артефакта урока на страницу ----------
// Контекст урока: переписывает относительные ссылки (Build It/Ship It/глоссарий)
// и собирает текстовые файлы урока, чтобы подшить их прямо в HTML страницы.
function makeLessonCtx(lessonAbsDir) {
  const docsAbsDir = path.join(lessonAbsDir, "docs");
  const collected = new Map(); // abs -> { slug, label, content, kind }
  const labelFor = (abs) => {
    const rel = path.relative(lessonAbsDir, abs);
    return rel.startsWith("..") ? path.relative(ROOT, abs) : rel;
  };
  const kindFor = (abs) => {
    const rel = path.relative(lessonAbsDir, abs);
    if (rel === "code" || rel.startsWith("code" + path.sep)) return "code";
    if (rel === "outputs" || rel.startsWith("outputs" + path.sep)) return "output";
    return "other";
  };
  const addFile = (abs) => {
    if (collected.has(abs)) return collected.get(abs).slug;
    let content;
    try { content = fs.readFileSync(abs, "utf8"); } catch (e) { return null; }
    const slug = slugify(path.relative(ROOT, abs));
    collected.set(abs, { slug, label: labelFor(abs), content, kind: kindFor(abs) });
    return slug;
  };
  const addDir = (abs) => {
    let first = null;
    for (const f of walkText(abs, []).sort()) { const s = addFile(f); if (!first) first = s; }
    return first;
  };
  // предварительно встраиваем весь код и артефакты урока (даже если на них нет ссылки)
  for (const sub of ["code", "outputs"]) {
    const d = path.join(lessonAbsDir, sub);
    if (fs.existsSync(d) && fs.statSync(d).isDirectory()) addDir(d);
  }
  const rewrite = (href) => {
    const h = href.trim();
    if (/^(https?:|mailto:|#)/i.test(h)) return { href: h, blank: /^https?:/i.test(h) };
    // tail без ведущих ../ ./ — в docs относительная глубина местами off-by-one,
    // поэтому переанкориваем хвост, а не доверяем числу «../».
    const tail = h.replace(/[#?].*$/, "").replace(/^(\.\.?\/)+/, "");
    if (/(^|\/)glossary\/terms\.md$/.test(tail)) return { href: "glossary.html", blank: false };
    for (const abs of [path.join(lessonAbsDir, tail), path.join(ROOT, tail)]) {   // урок, затем корень репо
      if (!abs.startsWith(ROOT) || !fs.existsSync(abs)) continue;
      const st = fs.statSync(abs);
      if (st.isDirectory()) return { href: "#" + (addDir(abs) || "lesson-files"), blank: false };
      if (isTextFile(abs)) { const s = addFile(abs); return { href: s ? "#" + s : h, blank: false }; }
    }
    return { href: h, blank: true };                                              // site-страницы (prereqs.html и т.п.), прочее — как есть
  };
  return { rewrite, collected };
}

// Подшивает собранные файлы как сворачиваемые блоки перед футером урока (последний <hr>).
function injectFiles(html, collected, exercise) {
  if (!collected || !collected.size) return html;
  const items = [...collected.values()];
  const isTest = (it) => it.kind === "code" && /(^|\/)test_|_test\.py$/.test(it.label);
  // В режиме упражнения: тесты — это ТЗ (раскрыты), эталонное решение — под катом.
  const groups = exercise
    ? [
        { pick: (it) => isTest(it),                       title: "Тесты — это твоё ТЗ", collapsed: false, note: "" },
        { pick: (it) => it.kind === "code" && !isTest(it), title: "Эталонное решение (Build It)", collapsed: true,
          note: "Сначала попробуй написать сам по спеке и тестам выше — потом раскрой и сверься." },
        { pick: (it) => it.kind === "output",             title: "Артефакт (Ship It)", collapsed: false, note: "" },
        { pick: (it) => it.kind === "other",              title: "Связанные файлы", collapsed: false, note: "" },
      ]
    : [
        { pick: (it) => it.kind === "code",   title: "Код урока (Build It)", collapsed: false, note: "" },
        { pick: (it) => it.kind === "output", title: "Артефакт (Ship It)",   collapsed: false, note: "" },
        { pick: (it) => it.kind === "other",  title: "Связанные файлы",       collapsed: false, note: "" },
      ];
  let sec = `<section class="lesson-files" id="lesson-files"><h2>Исходники урока</h2>`
    + `<p class="muted">Код и артефакт встроены прямо здесь — открывать GitHub не нужно.</p>`;
  if (exercise) {
    sec += `<div class="three-ways"><h3>Три пути пройти упражнение</h3><ol>`
      + `<li><strong>Собери сам</strong> — так глубже всего поймёшь, как это работает.</li>`
      + `<li><strong>Подсмотри эталон</strong> ниже, если застрял.</li>`
      + `<li><strong>Делегируй ИИ</strong> — напиши промпт и <strong>сам проверь</strong> результат тестами и глазами. `
      + `<button type="button" class="ai-prompt-btn">Скопировать промпт для ИИ</button></li>`
      + `</ol><p class="muted">Тесты — общий критерий приёмки на любом пути. Третий путь тренирует 4D: `
      + `Delegation · Description · Discernment · Diligence.</p></div>`;
  }
  for (const g of groups) {
    const part = items.filter(g.pick);
    if (!part.length) continue;
    sec += `<h3>${g.title}</h3>`;
    if (g.note) sec += `<p class="muted files-note">${g.note}</p>`;
    for (const it of part) {
      const hint = g.collapsed ? `<span class="reveal">Показать решение</span>` : "";
      const testAttr = isTest(it) ? ` data-test="1"` : "";
      sec += `<details class="filebox" id="${it.slug}"${g.collapsed ? "" : " open"}${testAttr}>`
        + `<summary><span class="fname">${esc(it.label)}</span>${hint}`
        + `<button type="button" class="copy-btn" title="Скопировать файл">Копировать</button></summary>`
        + `<pre><code>${esc(it.content)}</code></pre></details>`;
    }
  }
  sec += `</section>`;
  const at = html.lastIndexOf("<hr>");
  return at >= 0 ? html.slice(0, at) + sec + html.slice(at) : html + sec;
}

// ---------- сборка PHASES из PROGRESS.md ----------
function build() {
  const lessons = findLessons();
  const rmeta = readmePhaseMeta();
  const progress = fs.readFileSync(path.join(ROOT, "PROGRESS.md"), "utf8").split("\n");
  const phases = [];
  let cur = null;
  for (const line of progress) {
    const ph = line.match(/^##\s+Фаза\s+(\d+)\.\s+(.+)$/);
    if (ph) {
      cur = { id: +ph[1], name: ph[2].trim(), lessons: [],
              hours: (rmeta[ph[1]] || {}).hours || null,
              outcome: (rmeta[ph[1]] || {}).outcome || "" };
      phases.push(cur); continue;
    }
    const ls = line.match(/^-\s+\[([ x])\]\s+([\d.]+)\s+(.+)$/);
    if (ls && cur) {
      const id = ls[2];
      const done = ls[1] === "x";
      const L = lessons[id];
      const lm = L ? lessonMeta(L.md) : { motto: "", hours: null };
      const quiz = L ? L.quiz : null;
      let html = "";
      if (L) {
        CTX = makeLessonCtx(path.join(ROOT, L.dir));
        html = mdToHtml(L.md);
        const exercise = /<!--\s*exercise\s*-->/.test(L.md);   // урок-упражнение: эталон под катом
        html = injectFiles(html, CTX.collected, exercise);
        CTX = null;
      }
      // тег-якорь {{quiz}} → монтажный блок (заполняется на клиенте из quiz)
      html = html.replace("<p>{{quiz}}</p>", quiz ? `<div class="quiz-section" data-lesson="${id}"></div>` : "");
      cur.lessons.push({
        id, title: ls[3].trim(), status: done ? "done" : "planned",
        motto: lm.motto, hours: lm.hours, dir: L ? L.dir : null, quiz, html,
      });
    }
  }
  const allLessons = phases.flatMap((p) => p.lessons);
  const meta = {
    title: "AI Native: From Scratch to Agentic Systems",
    phases: phases.length,
    lessons: allLessons.length,
    done: allLessons.filter((l) => l.status === "done").length,
    hours: phases.reduce((s, p) => s + (p.hours || 0), 0),
    built: new Date().toISOString().slice(0, 10),
  };
  return { phases, meta };
}

function main() {
  const { phases, meta } = build();
  const glossary = readGlossary();
  const out = "/* СГЕНЕРИРОВАНО build.js — не редактировать вручную. */\n"
    + "const META = " + JSON.stringify(meta, null, 2) + ";\n"
    + "const PHASES = " + JSON.stringify(phases) + ";\n"
    + "const GLOSSARY = " + JSON.stringify(glossary) + ";\n";
  fs.writeFileSync(path.join(__dirname, "data.js"), out);
  console.log(`data.js: фаз ${meta.phases}, уроков ${meta.lessons} (готово ${meta.done}), ~${meta.hours} ч, глоссарий ${glossary.length}`);
}
main();
