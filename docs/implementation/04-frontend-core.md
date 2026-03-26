# Frontend Core — SPA Vanilla JS + PWA

> Última actualització: Març 2026

---

## Filosofia

**Zero dependencies. Zero build step. Zero frameworks.**

La app corre directament al navegador. No hi ha webpack, Vite, React, Vue ni TypeScript. Cada mòdul és un fitxer JS que s'importa dinàmicament quan cal. L'avantatge: menys complexitat, menys coses que trencar, desplegament trivial (copiar fitxers estàtics a Nginx).

---

## Estructura

```
frontend/
├── core/               ← NI UN SOL CANVI AQUÍ
│   ├── router.js         Hash SPA router (#/dashboard, #/portfolio, etc.)
│   ├── api.js            HTTP client centralitzat (fetch wrapper)
│   ├── store.js          Estat global reactiu via events
│   └── events.js         Event bus (on/off/emit/once)
├── modules/            ← Cada pantalla = nova carpeta
│   ├── dashboard/
│   ├── portfolio/
│   ├── simulation/
│   ├── history/
│   ├── analytics/
│   └── config/
├── css/
│   ├── variables.css     Design tokens (colors, tipografia, spacing)
│   ├── base.css          Reset + estils globals
│   └── components.css    Cards, badges, nav, skeletons, toasts
├── index.html            Entry point PWA
├── manifest.json         PWA manifest
└── service-worker.js     Cache estratègia (cache-first estàtics, network-first API)
```

---

## `core/router.js` — Hash Router

Navega entre vistes via hash: `window.location.hash = "#/dashboard"`.

```javascript
// Afegir una nova ruta:
const routes = {
    "/dashboard": () => import("/modules/dashboard/index.js"),
    "/portfolio": () => import("/modules/portfolio/index.js"),
    // ...
    "/nova-pantalla": () => import("/modules/nova-pantalla/index.js"),
};
```

Cada ruta carrega el mòdul lazily (primera visita) i l'injecta al `#app` container. El router renderitza automàticament la bottom navigation bar amb SVG icons.

---

## `core/api.js` — HTTP Client

```javascript
// Ús en qualsevol mòdul:
const data = await API.get("/api/v1/portfolio/summary");
await API.post("/api/v1/sync/upload", formData);
await API.put("/api/v1/config/assets/1", { target_weight: 25 });
```

Comportament automàtic:
- Emet `api:loading` (start/end) per a loading indicators globals
- Emet `api:error` si el servidor retorna error, perquè qualsevol mòdul pugui mostrar un toast
- Base URL configurable via `window.API_BASE_URL` (útil per a dev vs prod)

---

## `core/events.js` — Event Bus

Permet comunicació entre mòduls sense acoplament directe:

```javascript
// Mòdul A publica:
Events.emit("portfolio:updated", { netWorth: 42000 });

// Mòdul B subscriu (pot estar en un fitxer completament diferent):
Events.on("portfolio:updated", ({ netWorth }) => {
    document.querySelector("#net-worth").textContent = `${netWorth}€`;
});
```

---

## `core/store.js` — Estat Global

Conté les dades que comparteixen múltiples mòduls:
- `store.portfolio` — net worth, assets, última actualització
- `store.user` — preferències
- `store.alerts` — alertes actives

Qualsevol canvi al store emet `store:changed:<clau>` via Events.

---

## Sistema de Disseny (Dark Theme)

`css/variables.css` defineix tots els design tokens:

```css
--color-bg: #0f1117          /* Fons principal */
--color-surface: #1a1d27     /* Cards */
--color-surface-2: #252836   /* Elements nested */
--color-primary: #6c63ff     /* Accent principal */
--color-success: #22c55e     /* Verd positiu */
--color-danger: #ef4444      /* Vermell negatiu */
--color-warning: #f59e0b     /* Groc alerta */
--font-sans: "DM Sans"       /* Text general */
--font-mono: "DM Mono"       /* Números i valors */
```

`css/components.css` té components reutilitzables:
- `.card` — contenidor amb shadow i border-radius
- `.badge` (+ `.badge--green`, `.badge--red`, `.badge--yellow`) — etiquetes d'estat
- `.btn`, `.btn--primary`, `.btn--ghost`
- `.pill-group` + `.pill` — selector de pestanyes
- `.bottom-nav` — barra de navegació fixa inferior (mobile-first)
- `.skeleton` — loading placeholder animat
- `.progress-bar` — barra de progrés per a objectius
- `.toast` — notificació temporal (success/error/info)

---

## PWA

`manifest.json` configura:
- `display: standalone` → sembla una app nativa quan s'instal·la
- `theme_color: #0f1117` → color de la status bar
- Icones múltiples mides (192px, 512px)

`service-worker.js` implementa:
- **Cache-first** per a assets estàtics (JS, CSS, fonts, imatges) → carrega instantàniament
- **Network-first** per a `/api/` → sempre dades fresques, fallback a caché si offline

Per instal·lar com a app a iPhone: Safari → Share → "Afegir a la pantalla d'inici".

---

## Com Afegir una Nova Pantalla

1. Crear `frontend/modules/nova-pantalla/index.js` amb una funció `mount(container)` que renderitzi la vista
2. Afegir la ruta al `router.js`:
   ```javascript
   "/nova-pantalla": () => import("/modules/nova-pantalla/index.js"),
   ```
3. Afegir l'entrada a la bottom nav si cal (directament a `router.js`)

**Total de canvis a fitxers existents: 1-2 línies.** Res del core es toca.

---

## Accés en Dispositiu Real (iPhone/iPad)

Sense cap configuració extra:
1. Mac i iPhone a la mateixa xarxa WiFi
2. Obrir `http://[IP-del-Mac]:8080` des de Safari de l'iPhone
3. Per simular en Chrome: DevTools → Toggle device toolbar → iPhone 14 Pro (390×844)
