// 學名比對狀況儀表板：讀 #ms-root 的 data-endpoint，向 get_match_stat 取資料後繪製。
// 月份下拉由後端回傳的 available_months 決定（只列有資料的月份）。
// 所有樣式經 CSSOM（element.style）設定，不產生 inline style 屬性，符合嚴格 CSP。
(function () {
  "use strict";

  var COLORS = { atrank: "#2f6b5e", higher: "#a7c4b7" };   // 依 category_key
  var UNMATCHED_COLOR = {
    partner: "#2f6b5e", ours: "#c2cbc4", review: "#8fa39a", both: "#a7c4b7", info: "#dfe4de"
  };
  var COMPARE_LABELS = [
    ["new_atrank", "新對到來源階層"], ["worse", "變差（原本對到來源階層）"],
    ["reason_changed", "未對到原因改變"], ["new_name", "新增未對到學名"]
  ];
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

  function kpi(big, lbl, sub, subCls) {
    var c = mk("div", "ms-card ms-kpi");
    c.appendChild(mk("div", "big", big));
    c.appendChild(mk("div", "lbl", lbl));
    if (sub) c.appendChild(mk("div", "sub " + (subCls || ""), sub));
    return c;
  }

  function signed(n) { return (n > 0 ? "+" : n < 0 ? "−" : "±") + num(Math.abs(n)); }

  // 前次比較說明：無前次 / 比對邏輯變更 / 正常差值
  function deltaText(d) {
    if (d.logic_changed) return ["本次比對邏輯更新，不與前次比較", "muted"];
    if (d.atrank_delta == null) return [d.prev_year_month ? "" : "尚無前次資料", "muted"];
    var up = d.atrank_delta >= 0;
    return [(up ? "▲ " : "▼ ") + (up ? "+" : "") + d.atrank_delta.toFixed(1) +
            "% 較前次（" + d.prev_year_month + "）", up ? "up" : "down"];
  }

  // 對到來源階層率趨勢（長條，比對邏輯變更的月份加標註）
  function trendCard(trend, current) {
    var c = mk("div", "ms-card ms-sec");
    c.appendChild(mk("div", "ms-h", "對到來源階層率 · 歷次趨勢"));
    var box = mk("div", "ms-trend");
    // 刻度自「歷次最低值往下取整 5%」起算，讓差異看得出來；最低到 0
    var lo = Math.min.apply(null, trend.map(function (t) { return t.atrank_rate; }));
    var base = Math.max(0, Math.floor((lo - 5) / 5) * 5);
    trend.forEach(function (t) {
      var col = mk("div", "ms-tcol" + (t.year_month === current ? " cur" : ""));
      col.title = t.year_month + "：" + t.atrank_rate.toFixed(1) + "%" +
                  (t.logic_changed ? "（比對邏輯更新）" : "");
      col.appendChild(mk("div", "tv", t.atrank_rate.toFixed(1)));
      var track = mk("div", "ms-ttrack");
      var bar = mk("div", "ms-tbar");
      bar.style.height = ((t.atrank_rate - base) / (100 - base) * 100) + "%";
      track.appendChild(bar);
      col.appendChild(track);
      col.appendChild(mk("div", "tm", t.year_month + (t.logic_changed ? " *" : "")));
      box.appendChild(col);
    });
    c.appendChild(box);
    var notes = [];
    if (base > 0) notes.push("長條刻度自 " + base + "% 起算。");
    if (trend.some(function (t) { return t.logic_changed; })) {
      notes.push("* 該次比對邏輯更新，與前次的差異不代表資料品質變化。");
    }
    if (notes.length) c.appendChild(mk("div", "ms-note", notes.join("　")));
    return c;
  }

  // 學名變化摘要（依 meta.json 的 compare）
  function compareCard(d) {
    var c = mk("div", "ms-card ms-sec");
    c.appendChild(mk("div", "ms-h", "學名變化 · 較前次（" + d.prev_year_month + "）"));
    var row = mk("div", "ms-cmp");
    COMPARE_LABELS.forEach(function (x) {
      var n = d.compare[x[0]] || 0;
      var item = mk("div", "ms-cmp-item" + (x[0] === "worse" && n > 0 ? " warn" : ""));
      item.appendChild(mk("div", "big", num(n)));
      item.appendChild(mk("div", "lbl", x[1] + "（學名數）"));
      row.appendChild(item);
    });
    c.appendChild(row);
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
    var dt = deltaText(d);
    row.appendChild(kpi(d.atrank_rate.toFixed(1) + "%", "對到來源提供的階層", dt[0], dt[1]));
    row.appendChild(kpi(d.overall_rate.toFixed(1) + "%", "整體對到"));
    row.appendChild(kpi(num(d.total), "記錄總筆數"));
    body.appendChild(row);

    // 品質光譜
    var qc = mk("div", "ms-card ms-sec");
    qc.appendChild(mk("div", "ms-h", "資料解析品質 · 以來源階層為基準"));
    var stack = mk("div", "ms-stack");
    spectrum.forEach(function (s) {
      stack.appendChild(fill(mk("span"), s.pct, COLORS[s.key] || "#5f9b86"));
    });
    if (unmatchedPct > 0) stack.appendChild(fill(mk("span"), unmatchedPct, UNMATCHED_BG));
    qc.appendChild(stack);

    var legend = mk("div", "ms-legend");
    spectrum.forEach(function (s) {
      var item = mk("div");
      item.appendChild(fill(mk("span", "sw"), null, COLORS[s.key] || "#5f9b86"));
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

    // 歷次趨勢（至少兩次才顯示）
    if ((d.trend || []).length > 1) body.appendChild(trendCard(d.trend, d.year_month));

    // 學名變化摘要
    if (d.compare) body.appendChild(compareCard(d));

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
        var v = mk("div", "v", num(r.records));
        if (r.prev_records != null) {
          var diff = (r.records || 0) - r.prev_records;
          // 未對到筆數減少為改善
          v.appendChild(mk("span", "d " + (diff < 0 ? "up" : diff > 0 ? "down" : "muted"),
                           "（" + signed(diff) + "）"));
        }
        barRow.appendChild(v);
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
    if (dl.noname) dc.appendChild(link("ms-dl alt", dl.noname, "無學名紀錄清單", false));
    if (dl.compare_category) dc.appendChild(link("ms-dl alt", dl.compare_category, "分類比較（較前次）", false));
    if (dl.compare_names) dc.appendChild(link("ms-dl alt", dl.compare_names, "學名變化清單（較前次）", false));
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

    var url = endpoint + "?unit=" + encodeURIComponent(g);
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