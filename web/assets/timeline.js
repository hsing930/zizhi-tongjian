/* 時間線：依各節年號標題的西元年排列，可依朝代篩選，可輸入年份跳轉。 */
(function () {
  "use strict";
  var el = KB.el;
  var tlEl = document.getElementById("tl");
  var statusEl = document.getElementById("status");
  var yearEl = document.getElementById("year");
  var dynEl = document.getElementById("dynasty");
  var jumpForm = document.getElementById("jump-form");
  var dynOf = {};

  KB.loadMeta().then(function (meta) {
    meta.juans.forEach(function (j) { dynOf[j.n] = j.dynasty; });
    meta.dynasties.forEach(function (d) {
      dynEl.appendChild(el("option", { value: d, text: d }));
    });
    var params = new URLSearchParams(location.search);
    if (params.get("dynasty")) dynEl.value = params.get("dynasty");
    if (params.get("y")) yearEl.value = params.get("y");

    function render() {
      var dyn = dynEl.value;
      var rows = meta.timeline.map(function (t, i) { return { t: t, i: i }; })
        .filter(function (r) { return !dyn || dynOf[r.t.juan] === dyn; });
      KB.clear(tlEl);
      rows.forEach(function (r) { tlEl.appendChild(row(r.t, r.i, meta)); });
      statusEl.textContent = "共 " + KB.fmtNum(rows.length) + " 條年號（另有 " +
        meta.timeline_unparsed + " 條年號無法解析西元年，未列入）";
      return rows;
    }

    dynEl.addEventListener("change", function () {
      render();
      history.replaceState(null, "", dynEl.value ? "timeline.html?dynasty=" + encodeURIComponent(dynEl.value) : "timeline.html");
    });

    jumpForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var target = parseYear(yearEl.value);
      if (target === null) {
        statusEl.textContent = "請輸入西元年，例如 -403、前403 或 956。";
        return;
      }
      var rows = render();
      var hit = rows.filter(function (r) { return r.t.y >= target; })[0] || rows[rows.length - 1];
      if (!hit) return;
      var node = document.getElementById("tl-" + hit.i);
      if (node) {
        node.scrollIntoView({ block: "center" });
        node.style.background = "var(--mark)";
        setTimeout(function () { node.style.background = ""; }, 1500);
        // 以 :target 留下位置，方便重新整理後仍在同一處
        history.replaceState(null, "", "#tl-" + hit.i);
      }
    });

    render();
    if (params.get("y")) jumpForm.dispatchEvent(new Event("submit", { cancelable: true }));
    if (location.hash) {
      var node = document.getElementById(location.hash.slice(1));
      if (node) node.scrollIntoView({ block: "center" });
    }
  }).catch(function (err) { KB.showError(tlEl, err); });

  function row(t, i, meta) {
    var juan = meta.juans[t.juan - 1];
    var secHead = t.heading || "";
    return el("li", { id: "tl-" + i },
      el("span", { class: "y", text: KB.fmtYear(t.y) }),
      el("div", null,
        el("div", { class: "label", text: t.label }),
        el("div", { class: "juan" },
          el("a", { href: "juan.html?n=" + t.juan + "&s=" + t.sec, text: KB.juanLabel(juan) + (secHead ? "　" + secHead : "") }))))
    );
  }

  /** 解析輸入：-403、前403、前 403 年、956、公元956 → 整數（前為負）。 */
  function parseYear(s) {
    s = (s || "").replace(/\s|年|西元|公元/g, "");
    if (!s) return null;
    var neg = false;
    if (s.charAt(0) === "前") { neg = true; s = s.slice(1); }
    else if (s.charAt(0) === "-" || s.charAt(0) === "−") { neg = true; s = s.slice(1); }
    else if (s.charAt(0) === "後") { s = s.slice(1); }
    if (!/^\d+$/.test(s)) return null;
    var n = parseInt(s, 10);
    return neg ? -n : n;
  }
})();
