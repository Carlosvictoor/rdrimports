// ── Navbar mobile toggle ──────────────────────────────────────────
const toggle = document.getElementById('navToggler');
const mobileNav = document.getElementById('navMobile');

if (toggle && mobileNav) {
  toggle.addEventListener('click', () => {
    mobileNav.classList.toggle('open');
    const icon = toggle.querySelector('i');
    if (mobileNav.classList.contains('open')) {
      icon.className = 'bi bi-x';
    } else {
      icon.className = 'bi bi-list';
    }
  });
}

// ── Navbar scroll shrink ──────────────────────────────────────────
const navbar = document.getElementById('mainNav');
if (navbar) {
  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      navbar.style.background = 'rgba(10,10,10,0.97)';
    } else {
      navbar.style.background = '';
    }
  });
}

// ── Add to cart AJAX (atualiza badge sem reload) ──────────────────
document.querySelectorAll('.add-cart-form').forEach(form => {
  form.addEventListener('submit', async (e) => {
    const btn = form.querySelector('button[type="submit"]');
    if (btn && btn.disabled) return;

    e.preventDefault();

    const url = form.action;
    const data = new FormData(form);

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: data,
      });

      if (res.ok) {
        const json = await res.json();
        const badge = document.getElementById('cartBadge');
        if (badge) badge.textContent = json.count;

        // Feedback visual no botão
        if (btn) {
          const original = btn.innerHTML;
          btn.innerHTML = '<i class="bi bi-check-lg"></i> Adicionado!';
          btn.style.background = '#28a745';
          setTimeout(() => {
            btn.innerHTML = original;
            btn.style.background = '';
          }, 1800);
        }
      } else {
        form.submit();
      }
    } catch {
      form.submit();
    }
  });
});

// ── Auto-dismiss flash messages ───────────────────────────────────
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => {
    el.style.transition = 'opacity 0.5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 500);
  });
}, 4000);
