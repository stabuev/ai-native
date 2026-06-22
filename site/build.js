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
function inline(text) {
  return text.split("`").map((part, i) => {
    if (i % 2 === 1) return "<code>" + esc(part) + "</code>";
    let s = esc(part);
    s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
      (m, t, u) => `<a href="${u}" target="_blank" rel="noopener">${t}</a>`);
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    return s;
  }).join("");
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
      if (m) map[m[1]] = { dir: `phases/${phase}/${lesson}`, md, title: m[2].trim() };
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
      cur.lessons.push({
        id, title: ls[3].trim(), status: done ? "done" : "planned",
        motto: lm.motto, hours: lm.hours, dir: L ? L.dir : null,
        html: L ? mdToHtml(L.md) : "",
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
