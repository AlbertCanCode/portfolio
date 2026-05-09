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

// Footer year
document.getElementById('year').textContent = new Date().getFullYear();
