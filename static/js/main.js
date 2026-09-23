(function () {
  const drawer = document.getElementById("mobile-drawer");
  const toggle = document.getElementById("menu-toggle");
  if (toggle && drawer) {
    toggle.addEventListener("click", function () {
      const open = drawer.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
    });
    drawer.addEventListener("click", function (e) {
      if (e.target === drawer) {
        drawer.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
      }
    });
  }

  // Player tabs
  document.querySelectorAll("[data-tabs]").forEach(function (root) {
    const buttons = root.querySelectorAll("[data-tab]");
    const panels = root.querySelectorAll("[data-panel]");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        const id = btn.getAttribute("data-tab");
        buttons.forEach((b) => b.classList.toggle("is-active", b === btn));
        panels.forEach((p) =>
          p.classList.toggle("is-active", p.getAttribute("data-panel") === id)
        );
      });
    });
  });

  // Checkout payment method panels
  const payRadios = document.querySelectorAll('input[name="method"]');
  function syncPayPanels() {
    const selected = document.querySelector('input[name="method"]:checked');
    document.querySelectorAll("[data-pay-panel]").forEach(function (panel) {
      const match =
        selected && panel.getAttribute("data-pay-panel") === selected.value;
      panel.classList.toggle("is-active", !!match);
    });
  }
  payRadios.forEach((r) => r.addEventListener("change", syncPayPanels));
  syncPayPanels();

  // Quiz timer
  const timerEl = document.getElementById("quiz-timer");
  const quizForm = document.getElementById("quiz-form");
  if (timerEl && quizForm) {
    let remaining = parseInt(timerEl.getAttribute("data-seconds") || "0", 10);
    const label = timerEl.querySelector("span");
    function tick() {
      if (remaining <= 0) {
        if (label) label.textContent = "0:00";
        quizForm.submit();
        return;
      }
      const m = Math.floor(remaining / 60);
      const s = remaining % 60;
      if (label) label.textContent = m + ":" + String(s).padStart(2, "0");
      remaining -= 1;
      window.setTimeout(tick, 1000);
    }
    tick();
  }

  // Mark complete via fetch when data-ajax
  document.querySelectorAll("form[data-complete]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.fetch) return;
      e.preventDefault();
      const fd = new FormData(form);
      fetch(form.action, {
        method: "POST",
        body: fd,
        headers: { "X-Requested-With": "XMLHttpRequest" },
      })
        .then((r) => r.json())
        .then(function (data) {
          const bar = document.querySelector("[data-progress-bar]");
          if (bar && data.progress != null) {
            bar.style.width = data.progress + "%";
            const label = document.querySelector("[data-progress-label]");
            if (label) label.textContent = data.progress + "% complete";
          }
          form.querySelector("button").textContent = "Completed ✓";
          form.querySelector("button").disabled = true;
        })
        .catch(function () {
          form.submit();
        });
    });
  });
})();
