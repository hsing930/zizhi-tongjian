/* 首頁：卷目錄，依朝代分組 */
(function () {
  "use strict";
  var el = KB.el;
  var groupsEl = document.getElementById("groups");
  var statsEl = document.getElementById("stats");

  KB.loadMeta().then(function (meta) {
    statsEl.appendChild(el("span", { text: "共 " + meta.juan_count + " 卷" }));
    statsEl.appendChild(el("span", { text: fmt(meta.event_total) + " 個事件" }));
    statsEl.appendChild(el("span", { text: fmt(meta.comment_total) + " 則論斷（臣光曰）" }));
    statsEl.appendChild(el("span", { text: meta.dynasties.length + " 段朝代" }));

    KB.clear(groupsEl);
    meta.dynasties.forEach(function (dyn) {
      var list = meta.juans.filter(function (j) { return j.dynasty === dyn; });
      if (!list.length) return;
      groupsEl.appendChild(el("h2", { id: "d-" + dyn, text: dyn + "（" + list[0].n + "–" + list[list.length - 1].n + " 卷）" }));
      var ul = el("ul", { class: "juan-list" });
      list.forEach(function (j) {
        ul.appendChild(el("li", null,
          el("a", { class: "name", href: "juan.html?n=" + j.n }, KB.juanLabel(j)),
          el("span", { class: "meta" },
            "事件 " + j.events + "　論斷 " + j.comments + "　節 " + j.sections.length)));
      });
      groupsEl.appendChild(ul);
    });
  }).catch(function (err) { KB.showError(groupsEl, err); });

  function fmt(n) { return KB.fmtNum(n); }
})();
