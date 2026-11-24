/* 共用工具：資料載入（含快取）、安全的 DOM 建構、年份格式。
 * 所有頁面皆以 HTML 版面 + 此檔 + 各頁腳本組成，不需後端。 */
(function () {
  "use strict";

  var cache = {};

  /** 讀取 JSON（快取）。直接以 file:// 開啟時 fetch 會失敗，給出提示。 */
  function getJSON(url) {
    if (!cache[url]) {
      cache[url] = fetch(url).then(function (r) {
        if (!r.ok) throw new Error("讀取失敗 " + url + "（HTTP " + r.status + "）");
        return r.json();
      }).catch(function (err) {
        delete cache[url];
        if (location.protocol === "file:") {
          throw new Error("請以本機 HTTP 服務開啟，而非直接開啟檔案。見 web/README.md。");
        }
        throw err;
      });
    }
    return cache[url];
  }

  function loadMeta() { return getJSON("data/meta.json"); }

  function loadJuan(n) {
    return getJSON("data/juan" + String(n).padStart(3, "0") + ".json");
  }

  /**
   * 預留：人物/地名資料（data/entities/，由另一子工作階段產生）。
   * 檔案不存在時回傳 null，網頁照常運作；日後可在閱讀頁中把人名連到對應條目。
   */
  function loadEntities() {
    return fetch("data/entities/index.json")
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });
  }

  /** 建立元素：el("p", {class: "x"}, "文字", childEl, ...)，文字一律以 textContent 寫入，避免注入。 */
  function el(tag, attrs) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        var v = attrs[k];
        if (v === null || v === undefined || v === false) return;
        if (k === "class") node.className = v;
        else if (k === "text") node.textContent = v;
        else if (k.indexOf("on") === 0 && typeof v === "function") node.addEventListener(k.slice(2), v);
        else node.setAttribute(k, v === true ? "" : v);
      });
    }
    function add(c) {
      if (c === null || c === undefined || c === false) return;
      if (Array.isArray(c)) { c.forEach(add); return; }
      node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    }
    for (var i = 2; i < arguments.length; i++) add(arguments[i]);
    return node;
  }

  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  /** 西元年格式：負數為前（前 403 年）。 */
  function fmtYear(y) {
    return y < 0 ? "前" + (-y) + " 年" : y + " 年";
  }

  /** 千分位（事件數等）。 */
  function fmtNum(n) { return Number(n).toLocaleString("zh-Hant"); }

  /** 顯示用的卷名：「第N卷 周紀一」。 */
  function juanLabel(j) {
    var m = (j.title || "").match(/\S*紀\S*/);
    return "第" + j.n + "卷" + (m ? "　" + m[0] : "");
  }

  function showError(container, err) {
    clear(container);
    container.appendChild(el("div", { class: "error" }, String(err && err.message || err)));
  }

  window.KB = {
    getJSON: getJSON,
    loadMeta: loadMeta,
    loadJuan: loadJuan,
    loadEntities: loadEntities,
    el: el,
    clear: clear,
    fmtYear: fmtYear,
    fmtNum: fmtNum,
    juanLabel: juanLabel,
    showError: showError
  };
})();
