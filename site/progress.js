/* progress.js — личный прогресс «пройдено мной» в localStorage (отдельно от готовности курса). */
const Progress = (function () {
  const KEY = "ai-native-progress";
  function load() { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } }
  function save(s) { localStorage.setItem(KEY, JSON.stringify(s)); }
  return {
    isDone(id) { return !!load()[id]; },
    toggle(id) { const s = load(); s[id] = !s[id]; if (!s[id]) delete s[id]; save(s); return !!s[id]; },
    set(id, v) { const s = load(); if (v) s[id] = true; else delete s[id]; save(s); },
    count() { return Object.keys(load()).length; },
    pct(total) { return total ? Math.round(this.count() / total * 100) : 0; },
  };
})();
