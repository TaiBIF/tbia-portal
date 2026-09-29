// 學名比對狀況儀表板：讀 #ms-root 的 data-endpoint，向 get_match_stat 取資料後繪製。
// 月份下拉由後端回傳的 available_months 決定（只列有資料的月份）。
// 所有樣式經 CSSOM（element.style）設定，不產生 inline style 屬性，符合嚴格 CSP。
(function () {
  "use strict";

  var COLORS = {
    "對到（來源階層）": "#2f6b5e",
    "僅對到上階（較來源退階）": "#a7c4b7"
  };
  var UNMATCHED_COLOR = {
    partner: "#2f6b5e", ours: "#c2cbc4", review: "#8fa39a", both: "#a7c4b7"
  };
  var UNMATCHED_BG = "#c2cbc4";

  function el(id) { return document.getElementById(id); }
  function mk(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function fill(node, w, bg) {
    if (w != null) node.style.width = w + "%";
    if (bg) node.style.background = bg;
    return node;
  }
  function num(n) { return (n || 0).toLocaleString(); }

  function populateMonths(sel, months, current) {
    if (!sel) return;
    sel.textContent = "";
    (months || []).forEach(function (m) {
      var o = mk("option", null, m); o.value = m; sel.appendChild(o);
    });
    if (current) sel.value = current;
  }

  function kpi(big, lbl) {
    var c = mk("div", "ms-card ms-kpi");
    c.appendChild(mk("div", "big", big));
    c.appendChild(mk("div", "lbl", lbl));
    return c;
  }

  function render(d) {
    var body = el("ms-body");
    body.textContent = "";
    el("ms-unit").textContent = d.rights_holder || d.group || "—";
    el("ms-ym").textContent = d.year_month || "—";

    if (d.empty) { body.appendChild(mk("div", "ms-empty", "本月尚無比對統計資料。")); return; }

    var spectrum = d.spectrum || [];
    var reasons = d.reasons || [];
    var maxr = Math.max.apply(null, reasons.map(function (r) { return r.records || 0; }).concat([1]));
    var unmatchedPct = Math.max(0, +(100 - d.overall_rate).toFixed(1));

    // KPI
    var row = mk("div", "ms-row");
    row.appendChild(kpi(d.atrank_rate.toFixed(1) + "%", "對到來源提供的階層"));
    row.appendChild(kpi(d.overall_rate.toFixed(1) + "%", "整體對到"));
    row.appendChild(kpi(num(d.total), "記錄總筆數"));
    body.appendChild(row);

    // 品質光譜
    var qc = mk("div", "ms-card ms-sec");
    qc.appendChild(mk("div", "ms-h", "資料解析品質 · 以來源階層為基準"));
    var stack = mk("div", "ms-stack");
    spectrum.forEach(function (s) {
      stack.appendChild(fill(mk("span"), s.pct, COLORS[s.label] || "#5f9b86"));
    });
    if (unmatchedPct > 0) stack.appendChild(fill(mk("span"), unmatchedPct, UNMATCHED_BG));
    qc.appendChild(stack);

    var legend = mk("div", "ms-legend");
    spectrum.forEach(function (s) {
      var item = mk("div");
      item.appendChild(fill(mk("span", "sw"), null, COLORS[s.label] || "#5f9b86"));
      item.appendChild(document.createTextNode(s.label + " " + s.pct + "%"));
      item.appendChild(mk("span", "n", num(s.records)));
      legend.appendChild(item);
    });
    if (unmatchedPct > 0) {
      var u = mk("div");
      u.appendChild(fill(mk("span", "sw"), null, UNMATCHED_BG));
      u.appendChild(document.createTextNode("未對到 " + unmatchedPct + "%"));
      legend.appendChild(u);
    }
    qc.appendChild(legend);
    body.appendChild(qc);

    // 未對到原因
    if (reasons.length) {
      var rc = mk("div", "ms-card ms-sec");
      rc.appendChild(mk("div", "ms-h", "未對到學名 · 依原因分類"));
      reasons.forEach(function (r) {
        var barRow = mk("div", "ms-bar");
        barRow.appendChild(mk("div", "nm", r.label));
        var track = mk("div", "ms-track");
        var w = Math.round((r.records || 0) / maxr * 100);
        track.appendChild(fill(mk("div", "ms-fill"), w, UNMATCHED_COLOR[r.responsibility] || UNMATCHED_BG));
        barRow.appendChild(track);
        barRow.appendChild(mk("div", "v", num(r.records)));
        rc.appendChild(barRow);
      });
      body.appendChild(rc);
    }

    // 下載
    var dc = mk("div", "ms-card ms-sec");
    dc.appendChild(mk("div", "ms-h", "下載清單"));
    var dl = d.downloads || {};
    function link(cls, href, text, blank) {
      var a = mk("a", cls, text); a.href = href;
      if (blank) a.target = "_blank"; else a.setAttribute("download", "");
      return a;
    }
    dc.appendChild(link("ms-dl", dl.partner, "夥伴可修清單", false));
    dc.appendChild(link("ms-dl alt", dl.taicol, "回報 TaiCOL 清單", false));
    dc.appendChild(link("ms-dl alt", dl.email, "比對狀況圖", true));
    body.appendChild(dc);
  }

  // repopulate=true 時（初次載入 / 換單位）用回傳的 available_months 重建月份下拉
  function load(root, ym, repopulate) {
    var endpoint = root.dataset.endpoint;
    var gEl = el("ms-group");
    var g = gEl ? gEl.value : "";
    var body = el("ms-body");
    body.textContent = "";
    if (!g) { body.appendChild(mk("div", "ms-empty", "尚無可顯示的單位。")); return; }
    body.appendChild(mk("div", "ms-empty", "載入中…"));

    var url = endpoint + "?group=" + encodeURIComponent(g);
    if (ym) url += "&year_month=" + encodeURIComponent(ym);

    fetch(url, { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (repopulate) populateMonths(el("ms-month"), d.available_months, d.year_month);
        render(d);
      })
      .catch(function () {
        body.textContent = "";
        body.appendChild(mk("div", "ms-empty", "載入失敗。"));
      });
  }

  function init() {
    var root = el("ms-root");
    if (!root) return;
    var gsel = el("ms-group");
    if (gsel && gsel.tagName === "SELECT") {
      gsel.addEventListener("change", function () { load(root, "", true); });  // 換單位 → 重載最新月
    }
    var msel = el("ms-month");
    if (msel) msel.addEventListener("change", function () { load(root, msel.value, false); });
    load(root, "", true);  // 初次：取最新月 + 帶回月份清單
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();