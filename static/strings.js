// strings.js — дребезжание «струн» .grid-col при наведении
(function () {
  const DURATION = 900;            // мс до полного затухания
  const FRAMES = 60;               // ключевых кадров на колебание
  const OMEGA = 2 * Math.PI * 3.5; // 3.5 периода: к концу sin = 0, без скачка
  const DECAY = 4;                 // скорость затухания
  const MAX_SHIFT = 14;            // px, предел отклонения

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const strings = new WeakMap();   // струна -> {plucks, animation}
  let lastX = null;
  let lastTime = 0;

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  // Суммарное отклонение от всех касаний, которые ещё звучат
  function shiftAt(plucks, time) {
    let shift = 0;
    for (const pluck of plucks) {
      const t = (time - pluck.start) / DURATION;
      if (t >= 0 && t <= 1) {
        shift += pluck.amplitude * Math.exp(-DECAY * t) * Math.sin(OMEGA * t);
      }
    }
    return clamp(shift, -MAX_SHIFT, MAX_SHIFT);
  }

  function toTransform(shift) {
    const skew = shift * 0.22;
    const scale = 1 + Math.abs(shift) * 0.0025;
    return `translateX(${shift.toFixed(2)}px) skewX(${skew.toFixed(2)}deg) scaleX(${scale.toFixed(4)})`;
  }

  function pluck(col, amplitude) {
    // Время кадра, а не performance.now(): от него же отсчитывается анимация
    const now = document.timeline.currentTime ?? performance.now();
    const state = strings.get(col) || { plucks: [], animation: null };
    state.plucks = state.plucks.filter(p => now - p.start < DURATION);
    state.plucks.push({ amplitude, start: now });

    // Новая анимация начинается с текущего отклонения струны,
    // поэтому замена старой проходит без рывка
    const frames = [];
    for (let i = 0; i <= FRAMES; i++) {
      frames.push({ transform: toTransform(shiftAt(state.plucks, now + (i / FRAMES) * DURATION)) });
    }

    if (state.animation) state.animation.cancel();
    state.animation = col.animate(frames, { duration: DURATION, easing: 'linear' });
    state.animation.startTime = now;
    state.animation.onfinish = () => col.classList.remove('is-ringing');
    col.classList.add('is-ringing');
    strings.set(col, state);
  }

  function init() {
    const cols = document.querySelectorAll('.grid-col');
    if (!cols.length || !Element.prototype.animate) return;

    window.addEventListener('pointermove', e => {
      lastX = e.clientX;
      lastTime = e.timeStamp;
    }, { passive: true });

    cols.forEach(col => {
      col.addEventListener('pointerenter', e => {
        if (reducedMotion.matches) return;

        // Струна отклоняется туда, куда двигался курсор, и тем сильнее,
        // чем быстрее движение
        const dx = lastX === null ? 0 : e.clientX - lastX;
        const dt = Math.max(e.timeStamp - lastTime, 1);
        const speed = Math.abs(dx) / dt;
        const direction = dx > 0 ? 1 : -1;
        pluck(col, direction * clamp(5 + speed * 6, 5, MAX_SHIFT));
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
