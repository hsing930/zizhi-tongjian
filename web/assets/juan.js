/* 卷閱讀頁：依節（帝號）與年號閱讀；事件編號可點；校勘注與論斷可展開。
 * URL：juan.html?n=卷號[&s=節序號]，可加 #ev-節-序號 或 #cm-節-序號 定位。 */
(function () {
  "use strict";
  var el = KB.el;
  var params = new URLSearchParams(location.search);
  var n = parseInt(params.get("n"), 10);
  var headEl = document.getElementById("head");
  var bodyEl = document.getElementById("body");
  var tocEl = document.getElementById("toc");

  if (!n || n < 1 || n > 294) {
    KB.showError(headEl, new Error("卷號不正確（應為 1–294）。"));
    return;
  }

  Promise.all([KB.loadMeta(), KB.loadJuan(n), KB.loadEntities()]).then(function (res) {
    var meta = res[0], data = res[1], entities = res[2];
    // entities 預留：日後若有 data/entities/index.json，可在此把人名/地名連到對應條目。
    void entities;
    var info = meta.juans[n - 1];
    document.title = KB.juanLabel(info) + " · 資治通鑑知識庫";
    renderHead(info, data);
    renderToc(data);
    renderBody(data);
    jumpToTarget();
  }).catch(function (err) {
    KB.showError(headEl, err);
  });

  function renderHead(info, data) {
    KB.clear(headEl);
    var prev = n > 1 ? el("a", { href: "juan.html?n=" + (n - 1) }, "← 第" + (n - 1) + "卷") : el("span");
    var next = n < 294 ? el("a", { href: "juan.html?n=" + (n + 1) }, "第" + (n + 1) + "卷 →") : el("span");
    headEl.appendChild(el("div", { class: "juan-top" },
      el("div", null,
        el("div", { class: "muted", text: info.dynasty }),
        el("h1", { text: KB.juanLabel(info) }),
        data.period ? el("div", { class: "muted", text: data.period }) : null),
      el("div", { class: "pager" }, prev, el("a", { href: "index.html" }, "卷目錄"), next)));
    headEl.appendChild(el("div", { class: "toolbar" },
      el("span", { class: "muted", text: info.events + " 事件 · " + info.comments + " 則論斷 · " + info.notes + " 條校勘" }),
      el("button", { type: "button", onclick: function () { setAllDetails(true); } }, "展開全部注記"),
      el("button", { type: "button", onclick: function () { setAllDetails(false); } }, "收合全部注記")));
  }

  function renderToc(data) {
    KB.clear(tocEl);
    data.sections.forEach(function (sec, si) {
      tocEl.appendChild(el("a", { href: "#sec-" + si, text: sec.heading || "（無題）" }));
      var yh = sec.year_heading ? sec.year_heading.replace(/（.*$/, "") : "";
      if (yh) tocEl.appendChild(el("a", { class: "yr", href: "#sec-" + si, text: yh }));
    });
  }

  function renderBody(data) {
    KB.clear(bodyEl);
    data.sections.forEach(function (sec, si) {
      bodyEl.appendChild(el("h2", { id: "sec-" + si, text: sec.heading || "（無題）" }));
      if (sec.year_heading) bodyEl.appendChild(el("div", { class: "year-heading", text: sec.year_heading }));

      var ol = el("ol", { class: "events" });
      var lastYear = null;
      sec.events.forEach(function (ev, ei) {
        var id = "ev-" + si + "-" + ei;
        var yearTag = (ev.year && ev.year !== lastYear) ? el("span", { class: "ev-year", text: ev.year }) : null;
        if (ev.year) lastYear = ev.year;
        ol.appendChild(el("li", { id: id },
          el("a", { class: "no", href: "#" + id, title: "本事件連結", text: String(ev.no) }),
          yearTag,
          el("span", { text: ev.text }),
          notesBlock(ev.notes)));
      });
      bodyEl.appendChild(ol);

      (sec.comments || []).forEach(function (cm, ci) {
        var id = "cm-" + si + "-" + ci;
        bodyEl.appendChild(el("blockquote", { class: "comment", id: id },
          el("div", { class: "tag", text: "臣光曰" + (cm.year ? "　〔" + cm.year + "〕" : "") }),
          el("div", { text: cm.text.replace(/^臣光曰[：:]\s*/, "") }),
          notesBlock(cm.notes)));
      });
    });
  }

  /** 校勘注：預設收合，點「校勘注」展開。 */
  function notesBlock(notes) {
    if (!notes || !notes.length) return null;
    return el("details", null,
      el("summary", { text: "校勘注（" + notes.length + "）" }),
      el("ul", null, notes.map(function (t) { return el("li", { text: t }); })));
  }

  function setAllDetails(open) {
    document.querySelectorAll("details").forEach(function (d) { d.open = open; });
  }

  function jumpToTarget() {
    var target = null;
    if (location.hash) {
      target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    } else if (params.get("s") !== null) {
      target = document.getElementById("sec-" + params.get("s"));
    }
    if (target) {
      // 內容為非同步渲染，瀏覽器的 :target 可能已錯過，故改以 .hl 類別標示定位處
      target.classList.add("hl");
      setTimeout(function () { target.classList.remove("hl"); }, 2500);
      target.scrollIntoView({ block: "start" });
    }
  }
})();
