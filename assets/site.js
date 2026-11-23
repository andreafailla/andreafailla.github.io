// Theme toggle, scroll reveal, research-map hover, searchable lists, nav highlight, BibTeX copy.
// No dependencies. Every feature degrades to a working static page without JS.
(function () {
  "use strict";
  var root = document.documentElement;
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };

  // ---------------------------------------------------------------- theme
  var toggle = document.querySelector("[data-theme-toggle]");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var dark = root.dataset.theme
        ? root.dataset.theme === "dark"
        : window.matchMedia("(prefers-color-scheme: dark)").matches;
      root.dataset.theme = dark ? "light" : "dark";
      try { localStorage.setItem("theme", root.dataset.theme); } catch (e) { /* storage blocked */ }
    });
  }

  // ---------------------------------------------------------------- reveal on scroll
  var reveals = $$(".reveal");
  var showAll = function () { reveals.forEach(function (el) { el.classList.add("in", "done"); }); };
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  }
  // Fail-safe: never leave content hidden (no observer, frozen timers, print, crawlers).
  setTimeout(showAll, 2500);
  window.addEventListener("beforeprint", showAll);

  // ---------------------------------------------------------------- research map
  $$(".hg-wrap").forEach(function (wrap) {
    var tip = wrap.querySelector(".hg-tip");
    var clear = function () {
      wrap.classList.remove("is-active");
      $$(".on", wrap).forEach(function (el) { el.classList.remove("on"); });
      if (tip) tip.hidden = true;
    };
    var highlightTopics = function (topics, nodeId) {
      clear();
      wrap.classList.add("is-active");
      topics.forEach(function (t) {
        $$('[data-topic="' + t + '"]', wrap).forEach(function (el) { el.classList.add("on"); });
        if (!nodeId) {
          $$(".node", wrap).forEach(function (n) {
            if ((" " + n.dataset.topics + " ").indexOf(" " + t + " ") !== -1) n.classList.add("on");
          });
        }
      });
      if (nodeId) {
        var node = wrap.querySelector('.node[data-node="' + nodeId + '"]');
        if (node) node.classList.add("on");
      }
    };
    var showTip = function (node) {
      if (!tip) return;
      var c = node.querySelector("circle").getBoundingClientRect();
      var w = wrap.getBoundingClientRect();
      tip.textContent = node.dataset.label;
      tip.style.left = (c.left + c.width / 2 - w.left) + "px";
      tip.style.top = (c.top - w.top) + "px";
      tip.hidden = false;
    };
    $$(".hub", wrap).forEach(function (hub) {
      var on = function () { highlightTopics([hub.dataset.topic]); };
      hub.addEventListener("mouseenter", on);
      hub.addEventListener("focus", on);
    });
    $$(".node", wrap).forEach(function (node) {
      var on = function () { highlightTopics(node.dataset.topics.split(" "), node.dataset.node); showTip(node); };
      node.addEventListener("mouseenter", on);
      node.addEventListener("focus", on);
    });
    // While a theme is selected in the publication filter, keep it highlighted on the map;
    // hover previews temporarily replace it and leaving the map restores it.
    var selected = "";
    var rest = function () { if (selected) highlightTopics([selected]); else clear(); };
    wrap.showTopic = function (topic) { selected = topic || ""; rest(); };
    wrap.addEventListener("mouseleave", rest);
    wrap.addEventListener("focusout", function (e) { if (!wrap.contains(e.relatedTarget)) rest(); });
  });

  // ---------------------------------------------------------------- searchable lists
  // A [data-filterable] section holds a search box, facet dropdowns (<select data-facet>),
  // and a scroll box [data-list] of [data-item]s tagged with data-facets="topic:x kind:y".
  $$("[data-filterable]").forEach(function (root) {
    var box = root.querySelector("[data-list]");
    var items = $$("[data-item]", box);
    var input = root.querySelector("[data-search-input]");
    var selects = $$("select[data-facet]", root);
    var status = root.querySelector("[data-status]");
    var empty = root.querySelector("[data-empty]");
    var noun = root.dataset.noun || "items";
    var state = { facets: {}, terms: [] };

    var apply = function () {
      var shown = 0;
      items.forEach(function (el) {
        var tags = " " + el.dataset.facets + " ";
        var ok = Object.keys(state.facets).every(function (f) {
          return !state.facets[f] || tags.indexOf(" " + f + ":" + state.facets[f] + " ") !== -1;
        }) && state.terms.every(function (t) { return el.dataset.search.indexOf(t) !== -1; });
        el.hidden = !ok;
        if (ok) shown++;
      });
      $$("[data-group]", box).forEach(function (g) { g.hidden = !g.querySelector("[data-item]:not([hidden])"); });
      if (empty) empty.hidden = shown > 0;
      if (status) {
        var filtered = shown !== items.length;
        status.textContent = filtered ? "Showing " + shown + " of " + items.length + " " + noun : items.length + " " + noun;
        status.classList.toggle("is-filtered", filtered);
      }
      selects.forEach(function (s) {
        s.value = state.facets[s.dataset.facet] || "";
        s.classList.toggle("is-on", !!s.value);
      });
      box.scrollTop = 0;
    };
    var setFacet = function (facet, value) {
      state.facets[facet] = value;
      if (facet === "topic") {
        try {
          var url = new URL(location.href);
          if (value) url.searchParams.set("topic", value); else url.searchParams.delete("topic");
          history.replaceState(null, "", url);
        } catch (e) { /* old browser */ }
      }
      apply();
    };
    root.setFacet = setFacet;
    selects.forEach(function (s) {
      s.addEventListener("change", function () {
        setFacet(s.dataset.facet, s.value);
        if (s.dataset.facet === "topic") {
          var map = document.querySelector(".hg-wrap");
          if (map && map.showTopic) map.showTopic(s.value);
        }
      });
    });
    if (input) {
      input.addEventListener("input", function () {
        state.terms = input.value.toLowerCase().split(/\s+/).filter(Boolean);
        apply();
      });
    }
    $$("[data-reset]", root).forEach(function (b) {
      b.addEventListener("click", function () {
        state.facets = {}; state.terms = [];
        if (input) input.value = "";
        setFacet("topic", "");
      });
    });
    var initial = new URLSearchParams(location.search).get("topic");
    var topicSelect = root.querySelector('select[data-facet="topic"]');
    if (initial && topicSelect && topicSelect.querySelector('option[value="' + initial + '"]')) {
      state.facets.topic = initial;
      var map = document.querySelector(".hg-wrap");
      if (map && map.showTopic) map.showTopic(initial);
    }
    apply();
  });

  // Theme labels in the map filter the publication list in place (and keep the theme highlighted).
  var pubRoot = document.getElementById("publications");
  if (pubRoot && pubRoot.setFacet) {
    $$(".hub").forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        pubRoot.setFacet("topic", link.dataset.topic);
        var map = link.closest(".hg-wrap");
        if (map && map.showTopic) map.showTopic(link.dataset.topic);
        pubRoot.querySelector(".list-tools").scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });
  }

  // ---------------------------------------------------------------- nav: highlight the section in view
  var navLinks = $$(".site-header nav a[data-nav]");
  var sections = navLinks.map(function (a) { return document.getElementById(a.dataset.nav); }).filter(Boolean);
  if (sections.length) {
    // Active = last section whose top passed 30% of the viewport; at the very bottom, the last one.
    var updateNav = function () {
      var line = window.innerHeight * 0.3;
      var atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
      var current = null, currentTop = -Infinity;
      sections.forEach(function (s) {
        var top = s.getBoundingClientRect().top;
        // Largest top above the line; side-by-side cards tie, and the first (left) one wins.
        if (top <= line && top > currentTop + 1) { current = s.id; currentTop = top; }
      });
      if (atBottom) current = sections[sections.length - 1].id;
      navLinks.forEach(function (a) {
        if (a.dataset.nav === current) a.setAttribute("aria-current", "location");
        else if (a.getAttribute("aria-current") === "location") a.removeAttribute("aria-current");
      });
    };
    window.addEventListener("scroll", updateNav, { passive: true });
    window.addEventListener("resize", updateNav);
    updateNav();
  }

  // ---------------------------------------------------------------- copy BibTeX
  $$("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var code = btn.parentElement.querySelector("code");
      if (!code || !navigator.clipboard) return;
      navigator.clipboard.writeText(code.textContent).then(function () {
        var label = btn.textContent;
        btn.textContent = "Copied";
        setTimeout(function () { btn.textContent = label; }, 1500);
      });
    });
  });
})();
