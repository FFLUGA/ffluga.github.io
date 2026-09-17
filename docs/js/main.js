// Mobile nav toggle
document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".main-nav");

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var isOpen = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", isOpen);
    });
  }

  // Publications filter (publications.html only) — filters by research-area tag
  var filterButtons = document.querySelectorAll(".filter-btn");
  var pubItems = document.querySelectorAll(".pub-item");
  var pubEmptyState = document.getElementById("pubEmptyState");

  if (filterButtons.length && pubItems.length) {
    filterButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        filterButtons.forEach(function (b) {
          b.classList.remove("active");
        });
        btn.classList.add("active");

        var filter = btn.getAttribute("data-filter");
        var visible = 0;

        pubItems.forEach(function (item) {
          var cats = (item.getAttribute("data-cats") || "").split(" ");
          var show = filter === "all" || cats.indexOf(filter) !== -1;
          item.style.display = show ? "" : "none";
          if (show) visible++;
        });

        if (pubEmptyState) {
          pubEmptyState.hidden = visible !== 0;
        }
      });
    });
  }

  // Contact form (placeholder submit handling — no backend wired up)
  var form = document.querySelector(".contact-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      alert("Thanks for reaching out! This form is a placeholder — connect it to an email service or backend to make it functional.");
      form.reset();
    });
  }

  // Gallery carousel (gallery.html only)
  var carousel = document.querySelector(".carousel");
  if (carousel) {
    var track = carousel.querySelector(".carousel-track");
    var slides = Array.prototype.slice.call(carousel.querySelectorAll(".carousel-slide"));
    var dots = Array.prototype.slice.call(carousel.querySelectorAll(".carousel-dot"));
    var prevBtn = carousel.querySelector(".carousel-prev");
    var nextBtn = carousel.querySelector(".carousel-next");
    var index = 0;

    function goTo(i) {
      index = (i + slides.length) % slides.length;
      track.style.transform = "translateX(-" + index * 100 + "%)";
      dots.forEach(function (dot, di) {
        dot.classList.toggle("active", di === index);
      });
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", function () {
        goTo(index - 1);
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener("click", function () {
        goTo(index + 1);
      });
    }

    dots.forEach(function (dot, di) {
      dot.addEventListener("click", function () {
        goTo(di);
      });
    });

    carousel.setAttribute("tabindex", "0");
    carousel.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") goTo(index - 1);
      if (e.key === "ArrowRight") goTo(index + 1);
    });

    // Basic touch swipe support
    var touchStartX = null;
    carousel.addEventListener("touchstart", function (e) {
      touchStartX = e.touches[0].clientX;
    });
    carousel.addEventListener("touchend", function (e) {
      if (touchStartX === null) return;
      var delta = e.changedTouches[0].clientX - touchStartX;
      if (delta > 40) goTo(index - 1);
      if (delta < -40) goTo(index + 1);
      touchStartX = null;
    });

    goTo(0);
  }

  // Flip cards (people.html — all cards except Principal Investigator)
  var flipCards = document.querySelectorAll(".flip-card");
  flipCards.forEach(function (card) {
    card.setAttribute("tabindex", "0");
    card.setAttribute("role", "button");
    card.setAttribute("aria-pressed", "false");

    function toggleFlip() {
      var flipped = card.classList.toggle("flipped");
      card.setAttribute("aria-pressed", flipped);
    }

    card.addEventListener("click", function (e) {
      if (e.target.closest("a")) return;
      toggleFlip();
    });

    card.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        toggleFlip();
      }
    });
  });

  // Instrumentation photo lightbox (index.html)
  var instrumentThumbs = document.querySelectorAll(".instrument-thumb");
  var lightbox = document.getElementById("instrumentLightbox");

  if (instrumentThumbs.length && lightbox) {
    var lightboxImg = lightbox.querySelector(".lightbox-img");
    var lightboxCaption = lightbox.querySelector(".lightbox-caption");
    var closeBtn = lightbox.querySelector(".lightbox-close");
    var lastFocused = null;

    function openLightbox(thumb) {
      lastFocused = thumb;
      lightboxImg.src = thumb.getAttribute("data-full");
      lightboxImg.alt = thumb.querySelector("img").alt;
      lightboxCaption.textContent = thumb.getAttribute("data-caption") || "";
      lightbox.hidden = false;
      closeBtn.focus();
    }

    function closeLightbox() {
      lightbox.hidden = true;
      lightboxImg.src = "";
      if (lastFocused) lastFocused.focus();
    }

    instrumentThumbs.forEach(function (thumb) {
      thumb.addEventListener("click", function () {
        openLightbox(thumb);
      });
    });

    closeBtn.addEventListener("click", closeLightbox);

    lightbox.addEventListener("click", function (e) {
      if (e.target === lightbox) closeLightbox();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !lightbox.hidden) closeLightbox();
    });
  }
});
