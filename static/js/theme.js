function toggleTheme() {
  document.body.classList.toggle('dark-mode');
  // small persistence
  if (document.body.classList.contains('dark-mode')) localStorage.setItem('dm','1');
  else localStorage.removeItem('dm');
}
window.addEventListener('DOMContentLoaded', ()=>{
  if (localStorage.getItem('dm')) document.body.classList.add('dark-mode');
});
