// Fade-in on scroll
const observer = new IntersectionObserver(
  (entries) => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
  { threshold: 0.1 }
);

document.querySelectorAll('.card, .skill-group, .about-card, .about-text, .hero-stats .stat')
  .forEach(el => { el.classList.add('fade-in'); observer.observe(el); });

// Nav highlight
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('nav ul a[href^="#"]');

window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(s => { if (window.scrollY >= s.offsetTop - 120) current = s.id; });
  navLinks.forEach(a => {
    a.classList.toggle('active', a.getAttribute('href') === `#${current}`);
  });
}, { passive: true });

// Back to top
const btn = document.getElementById('backToTop');
window.addEventListener('scroll', () => {
  btn.classList.toggle('visible', window.scrollY > 400);
}, { passive: true });
btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// Typed hero text
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

// Project filter
const filterBtns = document.querySelectorAll('.filter-btn');
const cards = document.querySelectorAll('.card');

cards.forEach(card => {
  const tags = [...card.querySelectorAll('.tag')].map(t => t.textContent.toLowerCase());
  const isWip = card.querySelector('.wip-badge');
  let filters = [];
  if (tags.some(t => ['html', 'css', 'javascript', 'python'].includes(t))) filters.push('web');
  else filters.push('scratch');
  if (isWip) filters.push('wip');
  card.dataset.filter = filters.join(' ');
});

filterBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    filterBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const f = btn.dataset.filter;
    cards.forEach(card => {
      const match = f === 'all' || card.dataset.filter.includes(f);
      card.classList.toggle('hidden', !match);
    });
  });
});

// Hamburger menu
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

// Footer year
document.getElementById('year').textContent = new Date().getFullYear();
