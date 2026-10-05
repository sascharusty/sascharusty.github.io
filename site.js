// Small enhancements only. The page is complete without this file.
(function () {
  "use strict";

  var reduce = function () {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  };

  function scrollToEl(el) {
    var y = el.getBoundingClientRect().top + window.scrollY - 24;
    window.scrollTo({ top: y, behavior: reduce() ? "auto" : "smooth" });
  }

  // Email: assembled only after a real click, so the address never sits in the
  // source or the rendered page for harvesters (including JS-rendering ones).
  var mail = document.getElementById("mail");
  if (mail) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "text-button";
    btn.textContent = "Show email address";
    btn.addEventListener("click", function (e) {
      if (!e.isTrusted) return;
      var user = ["sas", "cha"].join("");
      var host = ["sascha", "rust"].join("") + "." + ["c", "om"].join("");
      var addr = user + String.fromCharCode(64) + host;
      var a = document.createElement("a");
      a.href = "mail" + "to:" + addr;
      a.textContent = addr;
      mail.replaceChildren(a);
      a.focus({ preventScroll: true });
    });
    mail.replaceChildren(btn);
  }

  // Article reader. Only runs when the Writing section is present.
  var writing = document.getElementById("writing");
  var articles = writing ? Array.prototype.slice.call(writing.querySelectorAll(".articles article")) : [];
  var list = writing && writing.querySelector(".list");

  var words = function (el) {
    return (el.querySelector(".body").textContent.trim().match(/\S+/g) || []).length;
  };
  var readTime = function (el) {
    return Math.max(1, Math.round(words(el) / 230)) + " min read";
  };
  var pad = function (n) { return String(n).padStart(2, "0"); };

  if (writing) {
    var count = writing.querySelector("[data-count]");
    if (count) count.textContent = pad(articles.length) + " · newest first";
    writing.querySelectorAll(".list .row").forEach(function (row) {
      var art = articles.find(function (a) { return a.dataset.slug === row.dataset.slug; });
      var rt = row.querySelector("[data-readtime]");
      if (art && rt) rt.textContent = readTime(art);
    });
  }

  var reader = null;
  var openIndex = null;

  function button(label, cls, onClick, disabled) {
    var b = document.createElement("button");
    b.type = "button";
    if (cls) b.className = cls;
    if (typeof label === "string") b.textContent = label; else b.append.apply(b, label);
    b.disabled = !!disabled;
    b.addEventListener("click", onClick);
    return b;
  }
  function span(cls, text) {
    var s = document.createElement("span");
    if (cls) s.className = cls;
    s.textContent = text;
    return s;
  }

  function render(i) {
    if (reader) { reader.remove(); reader = null; }
    openIndex = i;
    if (i === null) { list.hidden = false; return; }
    var src = articles[i];
    var hasPrev = i > 0, hasNext = i < articles.length - 1;

    reader = document.createElement("article");
    reader.className = "reader";
    reader.tabIndex = -1;

    var bar = document.createElement("nav");
    bar.className = "reader-bar";
    var right = document.createElement("div");
    right.className = "right";
    right.append(
      span("mono muted", pad(i + 1) + "/" + pad(articles.length)),
      button("← Previous", "text-button", function () { go(i - 1); }, !hasPrev),
      button("Next →", "text-button", function () { go(i + 1); }, !hasNext)
    );
    bar.append(button("← All writing", "text-button", function () { go(null); }), right);

    var head = document.createElement("header");
    head.className = "reader-head";
    var title = src.querySelector(".article-title").cloneNode(true);
    var meta = document.createElement("div");
    meta.className = "reader-meta mono muted";
    meta.append(span("", src.dataset.date), span("", src.dataset.venue), span("", readTime(src)));
    head.append(title, meta, src.querySelector(".dek").cloneNode(true));

    var pager = document.createElement("footer");
    pager.className = "pager";
    var titleOf = function (n) { return articles[n].querySelector(".article-title").textContent; };
    if (hasPrev) pager.append(button([span("mono muted", "← Previous"), span("pager-title", titleOf(i - 1))], "prev", function () { go(i - 1); }));
    if (hasNext) pager.append(button([span("mono muted", "Next →"), span("pager-title", titleOf(i + 1))], "next", function () { go(i + 1); }));

    reader.append(bar, head, src.querySelector(".body").cloneNode(true), pager);
    list.hidden = true;
    list.after(reader);
  }

  function go(i, fromHistory) {
    if (i !== null && (i < 0 || i >= articles.length)) return;
    var hash = i === null ? "#writing" : "#writing/" + articles[i].dataset.slug;
    if (!fromHistory && location.hash !== hash) history.pushState(null, "", hash);
    render(i);
    requestAnimationFrame(function () {
      var el = i === null ? list : reader;
      scrollToEl(el);
      if (i !== null) el.focus({ preventScroll: true });
    });
  }

  function fromHash() {
    var m = location.hash.match(/^#writing\/(.+)$/);
    var i = m ? articles.findIndex(function (a) { return a.dataset.slug === m[1]; }) : -1;
    if (i > -1) go(i, true);
    else if (openIndex !== null) render(null);
  }

  if (writing && articles.length) {
    list.querySelectorAll(".row").forEach(function (row) {
      row.addEventListener("click", function (e) {
        var i = articles.findIndex(function (a) { return a.dataset.slug === row.dataset.slug; });
        if (i > -1) { e.preventDefault(); go(i); }
      });
    });
    window.addEventListener("popstate", fromHash);
    window.addEventListener("hashchange", fromHash);
    document.addEventListener("keydown", function (e) {
      if (openIndex === null) return;
      if (e.key === "Escape") go(null);
      if (e.key === "ArrowRight") go(openIndex + 1);
      if (e.key === "ArrowLeft") go(openIndex - 1);
    });
    if (/^#writing\//.test(location.hash)) fromHash();
  }

  // Header links: "Writing" also closes an open article.
  document.querySelectorAll("[data-scroll]").forEach(function (a) {
    a.addEventListener("click", function (e) {
      var el = document.getElementById(a.dataset.scroll);
      if (!el) return;
      e.preventDefault();
      if (a.dataset.scroll === "writing" && openIndex !== null) render(null);
      history.pushState(null, "", "#" + a.dataset.scroll);
      scrollToEl(el);
    });
  });
})();
