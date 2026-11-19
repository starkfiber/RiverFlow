/* Presentation and a guided JavaScript quiz. No RF2 source evaluation or native execution. */
(() => {
  const progress = document.querySelector('#reading-progress');
  let frame = 0;
  const paintProgress = () => {
    frame = 0;
    const distance = document.documentElement.scrollHeight - innerHeight;
    if (progress) progress.style.transform = `scaleX(${distance > 0 ? Math.min(1, Math.max(0, scrollY / distance)) : 0})`;
  };
  const requestProgress = () => { if (!frame) frame = requestAnimationFrame(paintProgress); };
  addEventListener('scroll', requestProgress, { passive: true });
  addEventListener('resize', requestProgress, { passive: true });
  paintProgress();
  const chapters = [...document.querySelectorAll('.header nav a[href^="#"]')];
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) if (entry.isIntersecting) {
        for (const link of chapters) {
          if (link.hash === `#${entry.target.id}`) link.setAttribute('aria-current', 'location');
          else link.removeAttribute('aria-current');
        }
      }
    }, { rootMargin: '-15% 0px -55% 0px', threshold: 0 });
    for (const link of chapters) { const target = document.querySelector(link.hash); if (target) observer.observe(target); }
  }
  const form = document.querySelector('#quiz-form');
  if (!form) return;
  const input = document.querySelector('#quiz-answer');
  const feedback = document.querySelector('#game-feedback');
  const consolePanel = document.querySelector('.game-console');
  const dots = [...document.querySelectorAll('#round-dots i')];
  let round = 1, score = 0, complete = false;
  const render = () => {
    document.querySelector('#game-round').textContent = complete ? 'THREE ROUNDS COMPLETE' : `ROUND ${round} OF 3`;
    document.querySelector('#game-score').textContent = `${score} / 30`;
    document.querySelector('#game-question').textContent = complete ? 'A small program. Your first score.' : `What is double ${round}?`;
    document.querySelector('#game-number').textContent = complete ? String(score) : String(round);
    document.querySelector('.game-equation>span:nth-child(2)').textContent = complete ? 'out of' : '× 2';
    document.querySelector('.game-equation>b').textContent = complete ? '30' : '?';
    form.hidden = complete;
    document.querySelector('#quiz-reset').hidden = false;
    consolePanel.classList.toggle('is-complete', complete);
    dots.forEach((dot, index) => dot.classList.toggle('current', !complete && index === round - 1));
  };
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (complete) return;
    const raw = input.value;
    if (!/^(0|[1-9][0-9]{0,19})$/.test(raw) || BigInt(raw) > 18446744073709551615n) {
      input.setAttribute('aria-invalid', 'true');
      feedback.textContent = /^(0|[1-9][0-9]{0,19})$/.test(raw) ? 'That number is too large. Try a smaller whole number.' : 'Use a whole number, such as 2. No decimals or extra zeros at the start.';
      input.focus();
      return;
    }
    input.removeAttribute('aria-invalid');
    const correct = BigInt(raw) === BigInt(round * 2);
    if (correct) score += 10;
    dots[round - 1].classList.add(correct ? 'correct' : 'incorrect');
    const previous = round;
    if (round === 3) complete = true;
    else round += 1;
    input.value = '';
    render();
    feedback.textContent = complete
      ? `Finished. Your score is ${score} out of 30. Change the RF2 source to make a different game.`
      : `${correct ? 'Correct!' : `Double ${previous} is ${previous * 2}. Keep practising.`} Round ${round} is ready.`;
    if (!complete) input.focus();
    else document.querySelector('#quiz-reset').focus();
  });
  input.addEventListener('input', () => input.removeAttribute('aria-invalid'));
  document.querySelector('#quiz-reset').addEventListener('click', () => {
    round = 1; score = 0; complete = false;
    input.value = '';
    input.removeAttribute('aria-invalid');
    dots.forEach(dot => dot.classList.remove('correct', 'incorrect', 'current'));
    feedback.textContent = 'Ten points for each correct answer.';
    render(); input.focus();
  });
  render();
})();
