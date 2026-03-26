/**
 * Router SPA basat en hash.
 * Per afegir una nova pàgina: registrar ruta + crear mòdul a /modules/[name]/
 * Ús: Router.navigate('/portfolio')
 */
import Events from './events.js';

const ROUTES = {
  '/':           () => import('/modules/dashboard/index.js'),
  '/dashboard':  () => import('/modules/dashboard/index.js'),
  '/portfolio':  () => import('/modules/portfolio/index.js'),
  '/simulation': () => import('/modules/simulation/index.js'),
  '/history':    () => import('/modules/history/index.js'),
  '/analytics':  () => import('/modules/analytics/index.js'),
  '/config':     () => import('/modules/config/index.js'),
};

const NAV_ITEMS = [
  { path: '/dashboard',  label: 'Inici',      icon: 'home' },
  { path: '/portfolio',  label: 'Cartera',     icon: 'pie-chart' },
  { path: '/simulation', label: 'Simulació',   icon: 'trending-up' },
  { path: '/history',    label: 'Historial',   icon: 'clock' },
  { path: '/config',     label: 'Config',      icon: 'settings' },
];

const ICONS = {
  'home':        '<polyline points="3 9 12 2 21 9"/><path d="M9 22V12h6v10M3 9v13h18V9"/>',
  'pie-chart':   '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>',
  'trending-up': '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
  'clock':       '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  'settings':    '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
};

const Router = (() => {
  let currentPath = null;

  function getPath() {
    const hash = window.location.hash.slice(1) || '/';
    return hash.startsWith('/') ? hash : `/${hash}`;
  }

  function renderNav(activePath) {
    const existing = document.querySelector('.bottom-nav');
    if (existing) existing.remove();

    const nav = document.createElement('nav');
    nav.className = 'bottom-nav';
    nav.innerHTML = NAV_ITEMS.map(({ path, label, icon }) => `
      <a class="nav-item${activePath === path ? ' active' : ''}"
         href="#${path}"
         data-path="${path}">
        <svg class="nav-icon" viewBox="0 0 24 24">
          ${ICONS[icon] || ''}
        </svg>
        <span>${label}</span>
      </a>
    `).join('');

    document.getElementById('app').appendChild(nav);
  }

  async function render(path) {
    if (path === currentPath) return;
    currentPath = path;

    const loader = ROUTES[path] || ROUTES['/'];
    const app = document.getElementById('app');

    // Crear o reutilitzar el contenidor de pàgina
    let page = document.getElementById('page');
    if (!page) {
      page = document.createElement('main');
      page.id = 'page';
      app.insertBefore(page, app.querySelector('.bottom-nav'));
    }

    page.innerHTML = '';

    // Eliminar loading screen si existeix
    document.getElementById('loading-screen')?.remove();

    renderNav(path);
    Events.emit('route:change', path);

    try {
      const mod = await loader();
      if (mod.default?.render) {
        mod.default.render(page);
      }
    } catch (err) {
      console.error('Error carregant mòdul:', path, err);
      page.innerHTML = `<div class="card" style="margin-top:2rem;text-align:center">
        <p class="text-muted">No s'ha pogut carregar aquesta pàgina.</p>
      </div>`;
    }
  }

  function init() {
    window.addEventListener('hashchange', () => render(getPath()));
    render(getPath());
  }

  return {
    init,
    navigate(path) {
      window.location.hash = path;
    },
  };
})();

window.Router = Router;
Router.init();
export default Router;
