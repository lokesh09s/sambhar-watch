// App page controls: previous / next / play buttons for the date slider. The slider itself is handled by app.js.
(function () {
  const slider = document.getElementById("date-slider");
  const play = document.getElementById("date-play");
  let timer = null;

  /** Move the slider by `step` dates (wrapping round) and tell app.js about it. */
  function move(step) {
    const count = Number(slider.max) + 1;
    slider.value = (Number(slider.value) + step + count) % count;
    slider.dispatchEvent(new Event("input"));
  }

  function stop() {
    clearInterval(timer);
    timer = null;
    play.textContent = "\u25B6";
    play.setAttribute("aria-label", "Play through the dates");
  }

  document.getElementById("date-prev").addEventListener("click", () => { stop(); move(-1); });
  document.getElementById("date-next").addEventListener("click", () => { stop(); move(1); });
  play.addEventListener("click", () => {
    if (timer) return stop();
    timer = setInterval(() => move(1), 1300);
    play.textContent = "\u275A\u275A";
    play.setAttribute("aria-label", "Pause");
  });
})();
