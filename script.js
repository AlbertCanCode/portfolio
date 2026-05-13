// ─── SCROLL FADE-IN ──────────────────────────────────────────────────────────
// Watches elements with .fade-in and adds .visible when they enter the viewport
const observer = new IntersectionObserver(
  (entries) => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
  { threshold: 0.1 }
);
document.querySelectorAll('.card, .skill-group, .about-card, .about-text, .hero-stats .stat')
  .forEach(el => { el.classList.add('fade-in'); observer.observe(el); });

// ─── NAV HIGHLIGHT ────────────────────────────────────────────────────────────
// Adds .active to the nav link matching the currently visible section
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('nav ul a[href^="#"]');
window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(s => { if (window.scrollY >= s.offsetTop - 120) current = s.id; });
  navLinks.forEach(a => {
    a.classList.toggle('active', a.getAttribute('href') === `#${current}`);
  });
}, { passive: true });

// ─── BACK TO TOP ──────────────────────────────────────────────────────────────
// Shows the button after scrolling 400px, smooth-scrolls back to top on click
const btn = document.getElementById('backToTop');
window.addEventListener('scroll', () => {
  btn.classList.toggle('visible', window.scrollY > 400);
}, { passive: true });
btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// ─── PAGE LOAD ANIMATION ──────────────────────────────────────────────────────
// Adds .loaded to body once everything is ready, triggering CSS fade-in
window.addEventListener('load', () => {
  document.body.classList.add('loaded');
});

// ─── SCROLL PROGRESS BAR ─────────────────────────────────────────────────────
// Fills the top progress bar based on how far down the page you've scrolled
const progressBar = document.getElementById('scrollProgress');
window.addEventListener('scroll', () => {
  const scrolled = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight) * 100;
  progressBar.style.width = scrolled + '%';
}, { passive: true });

// ─── TYPED HERO TEXT ──────────────────────────────────────────────────────────
// Cycles through words in the hero headline with a typewriter effect
const words = ['games.', 'web apps.', 'pixel art.', 'platformers.', 'simulators.'];
let wi = 0, ci = 0, deleting = false;
const el = document.getElementById('typedText');
function type() {
  const word = words[wi];
  el.textContent = deleting ? word.slice(0, ci--) : word.slice(0, ci++);
  if (!deleting && ci === word.length + 1) { deleting = true; setTimeout(type, 1400); return; }
  if (deleting && ci === 0) { deleting = false; wi = (wi + 1) % words.length; }
  setTimeout(type, deleting ? 60 : 100);
}
type();

// ─── PROJECT FILTER ───────────────────────────────────────────────────────────
// Auto-assigns data-filter to each card based on its tags, then handles clicks
const filterBtns = document.querySelectorAll('.filter-btn');
const cards = document.querySelectorAll('.card');

// Assign filter categories from tag content
cards.forEach(card => {
  const tags = [...card.querySelectorAll('.tag')].map(t => t.textContent.toLowerCase());
  const isWip = card.querySelector('.wip-badge');
  let filters = [];
  if (tags.some(t => ['html', 'css', 'javascript', 'python'].includes(t))) filters.push('web');
  else filters.push('scratch');
  if (isWip) filters.push('wip');
  card.dataset.filter = filters.join(' ');
});

// Inject live counts into each filter button label
filterBtns.forEach(btn => {
  const f = btn.dataset.filter;
  const count = f === 'all'
    ? cards.length
    : [...cards].filter(c => c.dataset.filter.includes(f)).length;
  btn.innerHTML = btn.textContent + `<span class="filter-count">${count}</span>`;
});

// Handle filter button clicks with smooth fade transition
filterBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    filterBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const f = btn.dataset.filter;
    cards.forEach(card => {
      clearTimeout(card._hideTimer);
      const match = f === 'all' || card.dataset.filter.includes(f);
      if (match) {
        card.classList.remove('hidden', 'card-fading');
      } else {
        card.classList.add('card-fading');
        // Wait for fade-out transition to finish before hiding from layout
        card._hideTimer = setTimeout(() => card.classList.add('hidden'), 280);
      }
    });
  });
});

// ─── HAMBURGER MENU ───────────────────────────────────────────────────────────
// Toggles mobile nav open/closed; auto-closes when a link is tapped
const toggle = document.getElementById('navToggle');
const menu = document.getElementById('navMenu');
toggle.addEventListener('click', () => {
  toggle.classList.toggle('open');
  menu.classList.toggle('open');
});
document.querySelectorAll('#navMenu a').forEach(a => {
  a.addEventListener('click', () => {
    toggle.classList.remove('open');
    menu.classList.remove('open');
  });
});

// ─── FOOTER YEAR ─────────────────────────────────────────────────────────────
// Keeps the copyright year current automatically
document.getElementById('year').textContent = new Date().getFullYear();

// ─── LIGHT / DARK MODE TOGGLE ────────────────────────────────────────────────
// Reads saved preference from localStorage, defaults to dark
const themeToggle = document.getElementById('themeToggle');
const themeIcon   = themeToggle.querySelector('.theme-icon');
const themeLabel  = themeToggle.querySelector('.theme-label');

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  themeIcon.textContent  = theme === 'light' ? '🌙' : '☀️';
  themeLabel.textContent = theme === 'light' ? 'Dark' : 'Light';
  localStorage.setItem('theme', theme);
}

// Apply saved preference (or dark by default) on load
applyTheme(localStorage.getItem('theme') || 'dark');

themeToggle.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme');
  applyTheme(current === 'light' ? 'dark' : 'light');
});

// ─── ANIMATED NUMBER COUNTERS ────────────────────────────────────────────────
// Counts up hero stats from 0 when they scroll into view (ease-out cubic curve)
const counters = document.querySelectorAll('.stat-num[data-target]');
const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    const el = entry.target;
    const target = parseFloat(el.dataset.target);
    const suffix = el.dataset.suffix || '';
    const decimals = target % 1 !== 0 ? 1 : 0; // 1 decimal for 1.5M, none for integers
    const duration = 1800;
    const start = performance.now();
    function update(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      el.textContent = (eased * target).toFixed(decimals) + suffix;
      if (progress < 1) requestAnimationFrame(update);
      else el.textContent = target.toFixed(decimals) + suffix;
    }
    requestAnimationFrame(update);
    counterObserver.unobserve(el); // only run once per element
  });
}, { threshold: 0.6 });
counters.forEach(c => counterObserver.observe(c));
