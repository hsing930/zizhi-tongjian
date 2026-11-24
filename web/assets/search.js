/* 全文搜尋：首次搜尋時讀取全部卷檔，在記憶體中建立扁平索引（事件與論斷），再逐筆比對。
 * 搜尋結果可直接跳轉到卷頁的對應事件或論斷。 */
(function () {
  "use strict";
  var el = KB.el;
  var PAGE = 100;
  var index = null;      // 全部紀錄的陣列
  var indexPromise = null;
  var statusEl = document.getElementById("status");
  var resultsEl = document.getElementById("results");
  var moreEl = document.getElementById("more");
  var form = document.getElementById("search-form");
  var qEl = document.getElementById("q");
  var scopeEl = document.getElementById("scope");

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = qEl.value.trim();
    var scope = scopeEl.value;
    var url = "search.html?q=" + encodeURIComponent(q) + (scope !== "all" ? "&scope=" + scope : "");
    history.replaceState(null, "", url);
    run(q, scope);
  });

  var params = new URLSearchParams(location.search);
  if (params.get("q")) {
    qEl.value = params.get("q");
    if (params.get("scope")) scopeEl.value = params.get("scope");
    run(qEl.value.trim(), scopeEl.value);
  }

  /** 建立索引：每則事件與論斷各一筆，附卷號、節序號、位置與年號。 */
  function buildIndex() {
    if (indexPromise) return indexPromise;
    indexPromise = KB.loadMeta().then(function (meta) {
      var total = meta.juan_count;
      var done = 0;
      var jobs = [];
      for (var n = 1; n <= total; n++) {
        jobs.push(KB.loadJuan(n).then(function (data) {
          done++;
          statusEl.textContent = "建立索引中… " + done + " / " + total + " 卷";
          return data;
        }));
      }
      return Promise.all(jobs).then(function (datas) {
        var recs = [];
        datas.forEach(function (data, idx) {
          var n = idx + 1;
          var juanName = "第" + n + "卷";
          data.sections.forEach(function (sec, si) {
            sec.events.forEach(function (ev, ei) {
              recs.push({ kind: "event", juan: n, juanName: juanName, sec: si,
                secName: sec.heading || "（無題）", yr: sec.year_heading || "",
                pos: ei, no: ev.no, text: ev.text, id: "ev-" + si + "-" + ei });
            });
            (sec.comments || []).forEach(function (cm, ci) {
              var t = cm.text.replace(/^臣光曰[：:]\s*/, "");
              recs.push({ kind: "comment", juan: n, juanName: juanName, sec: si,
                secName: sec.heading || "（無題）", yr: sec.year_heading || "",
                pos: ci, no: null, text: t, id: "cm-" + si + "-" + ci });
            });
          });
        });
        // 預先轉小寫以便比對（中文不受影響）
        recs.forEach(function (r) { r.low = r.text.toLowerCase(); });
        index = recs;
        return recs;
      });
    });
    return indexPromise;
  }

  function run(q, scope) {
    KB.clear(resultsEl);
    KB.clear(moreEl);
    if (!q) {
      statusEl.textContent = "請輸入關鍵字。";
      return;
    }
    statusEl.textContent = "載入中…";
    buildIndex().then(function (recs) {
      var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
      var hits = recs.filter(function (r) {
        if (scope !== "all" && r.kind !== scope) return false;
        for (var i = 0; i < terms.length; i++) {
          if (r.low.indexOf(terms[i]) === -1) return false;
        }
        return true;
      });
      statusEl.textContent = "共 " + KB.fmtNum(hits.length) + " 則結果";
      renderHits(hits, terms, 0);
    }).catch(function (err) {
      statusEl.textContent = "";
      KB.showError(resultsEl, err);
    });
  }

  function renderHits(hits, terms, from) {
    var to = Math.min(hits.length, from + PAGE);
    for (var i = from; i < to; i++) resultsEl.appendChild(resultNode(hits[i], terms));
    KB.clear(moreEl);
    if (to < hits.length) {
      moreEl.appendChild(el("button", { type: "button", onclick: function () {
        KB.clear(moreEl);
        renderHits(hits, terms, to);
      } }, "顯示更多（還有 " + KB.fmtNum(hits.length - to) + " 則）"));
    }
  }

  function resultNode(r, terms) {
    var href = "juan.html?n=" + r.juan + "&s=" + r.sec + "#" + r.id;
    var where = [r.juanName, r.secName, r.yr.replace(/（.*$/, "")].filter(Boolean).join(" · ");
    var label = r.kind === "event" ? "事件 " + (r.no || "") : "臣光曰";
    return el("div", { class: "result" },
      el("div", { class: "where" },
        el("span", { class: "kind", text: label }),
        el("a", { href: href, text: where })),
      el("div", { class: "snippet" }, highlight(snippet(r.text, terms[0]), terms)));
  }

  /** 取關鍵字前後約 60 字作為摘要。 */
  function snippet(text, term) {
    var i = term ? text.toLowerCase().indexOf(term) : -1;
    if (i < 0 || text.length <= 120) return text.length > 120 ? text.slice(0, 120) + "…" : text;
    var start = Math.max(0, i - 50);
    var end = Math.min(text.length, i + term.length + 60);
    return (start > 0 ? "…" : "") + text.slice(start, end) + (end < text.length ? "…" : "");
  }

  /** 以 <mark> 標示關鍵字（節點建構，不使用 innerHTML）。 */
  function highlight(text, terms) {
    var frag = document.createDocumentFragment();
    var lower = text.toLowerCase();
    var marks = [];
    terms.forEach(function (t) {
      var from = 0, p;
      while ((p = lower.indexOf(t, from)) !== -1) { marks.push([p, p + t.length]); from = p + t.length; }
    });
    marks.sort(function (a, b) { return a[0] - b[0]; });
    var pos = 0;
    marks.forEach(function (m) {
      if (m[0] < pos) return;
      if (m[0] > pos) frag.appendChild(document.createTextNode(text.slice(pos, m[0])));
      frag.appendChild(el("mark", { text: text.slice(m[0], m[1]) }));
      pos = m[1];
    });
    if (pos < text.length) frag.appendChild(document.createTextNode(text.slice(pos)));
    return frag;
  }
})();
