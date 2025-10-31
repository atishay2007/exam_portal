// quiz timer and auto-submit
let timeLeft = document.getElementById('timeLeft');
let timerInterval;
function startTimer(seconds) {
  let t = seconds;
  if (timerInterval) clearInterval(timerInterval);
  timeLeft && (timeLeft.innerText = t);
  timerInterval = setInterval(()=> {
    t -= 1;
    if(timeLeft) timeLeft.innerText = t;
    if (t <= 0) {
      clearInterval(timerInterval);
      // auto submit form if present
      const form = document.getElementById('answerForm');
      if (form) form.submit();
    }
  }, 1000);
}

// progress bar
function setProgress(p) {
  const bar = document.getElementById('progBar');
  if (bar) bar.style.width = p + '%';
}
