#!/usr/bin/env node
/* build.js — генератор статичного сайта курса AI Native.
 *
 * Источник правды: PROGRESS.md (фазы, уроки, статус), phases/<...>/docs/ru.md
 * (контент уроков), README.md (часы и результат фазы). Рендерит каждый урок из
 * Markdown в HTML и пишет site/data.js (PHASES, GLOSSARY, META). Без зависимостей.
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

const GLOSSARY = [
  ["Токен", "Кусок текста, которым оперирует модель", "Не слово и не символ: текст бьётся на токены по статистике (BPE). Платишь и считаешь бюджет в токенах (урок 1.1)."],
  ["Контекстное окно", "Сколько токенов модель видит за раз", "Конечный бюджет: system + история + RAG + ответ. Вышло за окно — модель не видит (уроки 1.2, 4.4)."],
  ["Inference", "Генерация ответа по одному токену", "Авторегрессивный цикл: предсказать токен → дописать → повторить. Отсюда стриминг (урок 1.2)."],
  ["Температура", "Степень случайности генерации", "T=0 — детерминированный argmax; выше — разнообразнее. На новых Claude не настраивается (урок 1.3)."],
  ["Галлюцинация", "Уверенно неверный ответ", "Модель предсказывает правдоподобное, а не истину. Лечится заземлением, цитатами, правом «не знаю» (уроки 1.4, 11.2)."],
  ["Промпт", "Интерфейс к модели", "Анатомия: роль, контекст, задача, формат, примеры. Воспроизводимость измеряется eval-harness (Фаза 2)."],
  ["Few-shot", "Примеры в промпте", "Показать 2–5 примеров вход→выход, чтобы задать формат/класс без дообучения (урок 2.2)."],
  ["Chain-of-Thought", "Пошаговое рассуждение", "«Думай по шагам» поднимает качество на многошаговых задачах (урок 2.2)."],
  ["RAG", "Найди нужное, потом ответь", "Retrieval + augmentation: подкладываем релевантные куски в промпт. Прод-версия — гибрид+rerank (уроки 3.3, 3.5)."],
  ["Эмбеддинг", "Представление текста числами", "Близкое по смыслу близко в пространстве; поиск по косинусу. Учебно — TF-IDF (урок 3.3)."],
  ["Векторное хранилище", "База для поиска по смыслу", "add/query/persist по эмбеддингам (Chroma/FAISS). Память RAG (урок 3.4)."],
  ["MCP", "Разъём ИИ ↔ инструменты", "Model Context Protocol: host ↔ client ↔ server, tools/resources/prompts, discovery (Фаза 6)."],
  ["Tool use", "Вызов инструментов моделью", "Function calling: модель просит инструмент по схеме, получает результат в цикле (уроки 6.1, 7.1)."],
  ["Агент", "Цикл reason → act → observe", "Не модель, а петля: policy выбирает действие, инструмент исполняет, результат в историю (урок 7.1)."],
  ["Guardrail", "Заслон перед действием", "Валидация + подтверждение опасного (human-in-the-loop) до исполнения (урок 7.3)."],
  ["Оркестратор", "Раздаёт роли субагентам", "Lead декомпозирует задачу, субагенты выполняют, lead сводит (Фаза 8)."],
  ["A2A", "Протокол агент ↔ агент", "Карточки возможностей (discovery) + конверт задачи. Дополняет MCP (урок 8.2)."],
  ["FinOps", "Экономика моделей", "Маршрутизация по сложности, каскад+кэш+batch, учёт и ROI «до/после» (Фаза 9)."],
  ["Observability", "Видимость работы агента", "Вложенные spans на шаги (как OpenTelemetry): где узкое место и где упало (урок 10.4)."],
  ["Prompt injection", "Перехват через данные", "Скрытая инструкция в данных/RAG (OWASP LLM01). Защита: allowlist, sanitize, человек (урок 11.5)."],
];

function main() {
  const { phases, meta } = build();
  const out = "/* СГЕНЕРИРОВАНО build.js — не редактировать вручную. */\n"
    + "const META = " + JSON.stringify(meta, null, 2) + ";\n"
    + "const PHASES = " + JSON.stringify(phases) + ";\n"
    + "const GLOSSARY = " + JSON.stringify(GLOSSARY.map(([term, says, means]) => ({ term, says, means }))) + ";\n";
  fs.writeFileSync(path.join(__dirname, "data.js"), out);
  console.log(`data.js: фаз ${meta.phases}, уроков ${meta.lessons} (готово ${meta.done}), ~${meta.hours} ч`);
}
main();
