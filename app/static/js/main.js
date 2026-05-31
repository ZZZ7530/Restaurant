document.documentElement.classList.add("js-enabled");

const heroCarousel = document.querySelector("[data-hero-carousel]");

if (heroCarousel) {
  const slides = Array.from(heroCarousel.querySelectorAll(".home-hero__image"));
  const previousButton = document.querySelector("[data-hero-prev]");
  const nextButton = document.querySelector("[data-hero-next]");
  const dots = Array.from(document.querySelectorAll("[data-hero-dot]"));
  const intervalMs = 10000;
  let currentIndex = slides.findIndex((slide) => slide.classList.contains("is-active"));
  let timerId = null;

  if (currentIndex < 0) {
    currentIndex = 0;
  }

  const showSlide = (index) => {
    if (!slides.length) {
      return;
    }

    currentIndex = (index + slides.length) % slides.length;

    slides.forEach((slide, slideIndex) => {
      slide.classList.toggle("is-active", slideIndex === currentIndex);
    });

    dots.forEach((dot, dotIndex) => {
      const isCurrent = dotIndex === currentIndex;
      dot.classList.toggle("is-active", isCurrent);
      dot.setAttribute("aria-current", isCurrent ? "true" : "false");
    });
  };

  const nextSlide = () => {
    showSlide(currentIndex + 1);
  };

  const previousSlide = () => {
    showSlide(currentIndex - 1);
  };

  const restartTimer = () => {
    window.clearInterval(timerId);

    if (slides.length > 1) {
      timerId = window.setInterval(nextSlide, intervalMs);
    }
  };

  previousButton?.addEventListener("click", () => {
    previousSlide();
    restartTimer();
  });

  nextButton?.addEventListener("click", () => {
    nextSlide();
    restartTimer();
  });

  dots.forEach((dot) => {
    dot.addEventListener("click", () => {
      showSlide(Number(dot.dataset.heroDot));
      restartTimer();
    });
  });

  showSlide(currentIndex);
  restartTimer();
}
