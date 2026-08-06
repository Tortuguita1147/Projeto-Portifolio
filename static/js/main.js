/**
 * Rayane Yasmin Fotografia — main.js
 * JS vanilla, sem dependências externas, carregado com `defer` para não
 * bloquear a renderização da página (bom para performance/Core Web Vitals).
 */
(function () {
  "use strict";

  /* ---------- Ano no rodapé ------------------------------------------- */
  var anoEl = document.getElementById("ano");
  if (anoEl) anoEl.textContent = new Date().getFullYear();

  /* ---------- Nav: fundo ao rolar + menu mobile ------------------------ */
  var nav = document.getElementById("nav");
  var toggle = document.getElementById("navToggle");
  var menu = document.getElementById("navMenu");

  function onScroll() {
    if (window.scrollY > 24) {
      nav.classList.add("is-scrolled");
    } else {
      nav.classList.remove("is-scrolled");
    }
  }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var isOpen = menu.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(isOpen));
    });

    // Fecha o menu mobile ao clicar em qualquer link
    menu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        menu.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ---------- FAQ: acordeão --------------------------------------------- */
  document.querySelectorAll(".accordion__trigger").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var panel = btn.nextElementSibling;
      var isOpen = btn.getAttribute("aria-expanded") === "true";

      // Fecha os demais itens (acordeão exclusivo)
      document.querySelectorAll(".accordion__trigger").forEach(function (other) {
        if (other !== btn) {
          other.setAttribute("aria-expanded", "false");
          other.nextElementSibling.style.maxHeight = null;
        }
      });

      btn.setAttribute("aria-expanded", String(!isOpen));
      panel.style.maxHeight = isOpen ? null : panel.scrollHeight + "px";
    });
  });

  /* ---------- Reveal ao rolar (IntersectionObserver) --------------------- */
  var revealTargets = document.querySelectorAll(
    ".card--on-green, .differential, .testimonial, .pricing-card, " +
    ".timeline__item, .gallery-card, .quote-card, .sobre__photo"
  );

  if ("IntersectionObserver" in window && revealTargets.length) {
    revealTargets.forEach(function (el) { el.classList.add("reveal"); });

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -60px 0px" }
    );

    revealTargets.forEach(function (el) { observer.observe(el); });
  }

  /* ---------- Galeria: modal ao clicar em qualquer card do bento ------- */
  var galleryCards = document.querySelectorAll("[data-gallery-card]");
  var modal = document.querySelector("[data-gallery-modal]");

  if (galleryCards.length || modal) {
    var modalTitle = modal.querySelector("#galleryModalTitle");
    var modalGrid = modal.querySelector("[data-gallery-grid]");
    var modalVideo = modal.querySelector("[data-gallery-video]");
    var modalVideoLink = modal.querySelector("[data-gallery-video-link]");
    var closeEls = modal.querySelectorAll("[data-gallery-close]");
    var lastFocusedEl = null;

    /* Abre o modal com uma lista de fotos (URLs) e um t\u00edtulo.
       Componente \u00fanico: usado pela home (categorias fixas) e pela
       galeria privada /galeria/<codigo> — ver "galeria privada" abaixo. */
    function abrirModalComFotos(title, fotos) {
      modalTitle.textContent = title;
      modalGrid.innerHTML = "";
      modalVideo.hidden = true;
      modalGrid.hidden = false;

      fotos.forEach(function (src) {
        var fig = document.createElement("div");
        fig.className = "gallery-modal__photo";
        fig.style.setProperty("--photo", "url('" + src + "')");
        modalGrid.appendChild(fig);
      });

      lastFocusedEl = document.activeElement;
      modal.hidden = false;
      // For\u00e7a reflow para a transi\u00e7\u00e3o de abertura funcionar.
      // eslint-disable-next-line no-unused-expressions
      modal.offsetHeight;
      modal.classList.add("is-open");
      document.body.style.overflow = "hidden";

      var closeBtn = modal.querySelector(".gallery-modal__close");
      if (closeBtn) closeBtn.focus();

      document.addEventListener("keydown", onKeydown);
    }

    /* Abre o modal com o conte\u00fado do card clicado: ou a grade com
       todas as refer\u00eancias do mesmo estilo, ou o link do YouTube
       quando o card clicado \u00e9 o de v\u00eddeo. */
    function openModal(card) {
      var title = card.getAttribute("data-cat-title") || "";
      var type = card.getAttribute("data-type") || "fotos";

      if (type === "video") {
        modalTitle.textContent = title;
        modalGrid.innerHTML = "";
        modalGrid.hidden = true;
        modalVideo.hidden = false;
        var url = card.getAttribute("data-video-url") || "#";
        if (modalVideoLink) modalVideoLink.setAttribute("href", url);

        lastFocusedEl = document.activeElement;
        modal.hidden = false;
        // eslint-disable-next-line no-unused-expressions
        modal.offsetHeight;
        modal.classList.add("is-open");
        document.body.style.overflow = "hidden";
        var closeBtn = modal.querySelector(".gallery-modal__close");
        if (closeBtn) closeBtn.focus();
        document.addEventListener("keydown", onKeydown);
        return;
      }

      var fotosRaw = card.getAttribute("data-fotos");
      var fotos = [];
      try {
        fotos = fotosRaw ? JSON.parse(fotosRaw) : [];
      } catch (e) {
        fotos = [];
      }
      abrirModalComFotos(title, fotos);
    }

    function closeModal() {
      modal.classList.remove("is-open");
      document.body.style.overflow = "";
      document.removeEventListener("keydown", onKeydown);

      window.setTimeout(function () {
        modal.hidden = true;
      }, 300);

      if (lastFocusedEl && typeof lastFocusedEl.focus === "function") {
        lastFocusedEl.focus();
      }
    }

    function onKeydown(e) {
      if (e.key === "Escape" || e.key === "Esc") {
        closeModal();
      }
    }

    galleryCards.forEach(function (card) {
      card.addEventListener("click", function () {
        openModal(card);
      });
    });

    /* ---------- Galeria privada (/galeria/<codigo>) --------------------
       As fotos do evento chegam serializadas em um JSON no template
       (id=galeria-privada-dados) e o modal é aberto com elas — mesmo
       componente visual da home, sem duplicação. */
    var dadosPrivada = document.getElementById("galeria-privada-dados");
    var gridPrivada = document.querySelector("[data-privada-titulo]");
    if (dadosPrivada && gridPrivada) {
      var fotosPrivadas = [];
      try {
        fotosPrivadas = JSON.parse(dadosPrivada.textContent) || [];
      } catch (e) {
        fotosPrivadas = [];
      }
      var tituloPrivada = gridPrivada.getAttribute("data-privada-titulo") || "Galeria";
      var cardsPrivados = gridPrivada.querySelectorAll("[data-privada-foto]");
      cardsPrivados.forEach(function (card) {
        card.addEventListener("click", function () {
          var urls = fotosPrivadas.map(function (f) { return f.url; });
          abrirModalComFotos(tituloPrivada, urls);
        });
      });
    }

    closeEls.forEach(function (el) {
      el.addEventListener("click", closeModal);
    });
  }
})();


