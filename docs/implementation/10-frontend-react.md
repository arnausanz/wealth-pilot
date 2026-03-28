# Frontend — React 18 + TypeScript + Vite

> Última actualització: Març 2026

---

## Stack tecnològic

| Eina | Versió | Funció |
|------|--------|--------|
| **React** | 18 | UI components i rendering |
| **TypeScript** | 5 | Tipus estàtics, seguretat en temps de compilació |
| **Vite** | 5 | Build tool + dev server amb HMR |
| **React Router** | v6 | Navegació SPA |
| **TanStack Query** | v5 | Server state, caching, refetch automàtic |
| **Zustand** | 5 | Client state (tema, UI preferences) |
| **Vitest** | 2 | Test runner (compatible amb Jest API) |
| **React Testing Library** | — | Tests de components |
| **jsdom** | — | DOM simulat per a tests |

---

## Estructura de fitxers

```
frontend/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
└── src/
    ├── main.tsx              ← Entry point: React + QueryClient + Router
    ├── App.tsx               ← Layout principal + bottom nav + routes
    ├── core/
    │   ├── api.ts            ← fetch wrapper centralitzat (baseURL, errors)
    │   └── queryClient.ts    ← TanStack QueryClient configurat
    ├── hooks/
    │   ├── useTheme.ts       ← Zustand store: isDark / toggle / setDark
    │   ├── useNetWorth.ts    ← TanStack Query: GET /api/v1/portfolio/networth
    │   └── useMarketPrices.ts← TanStack Query: GET /api/v1/market/prices
    ├── types/
    │   └── index.ts          ← Tots els tipus TypeScript + helper n()
    ├── components/
    │   ├── ui/
    │   │   ├── Card.tsx      ← Glass card container
    │   │   ├── NavBar.tsx    ← Bottom navigation bar
    │   │   ├── StatusDot.tsx ← Indicador de connexió (live/stale/error)
    │   │   └── TimeSelector.tsx ← Pills de periode (1S/1M/3M/6M/1A/MAX)
    │   └── charts/
    │       ├── PortfolioChart.tsx ← SVG line chart amb animació morphing
    │       ├── DonutChart.tsx     ← SVG donut (distribució d'actius)
    │       └── GoalRing.tsx       ← SVG ring (progrés objectiu)
    ├── features/
    │   ├── dashboard/
    │   │   ├── DashboardScreen.tsx ← Pantalla principal
    │   │   ├── HeroValue.tsx       ← Valor total + variació
    │   │   ├── ChartSection.tsx    ← Gràfic + TimeSelector
    │   │   ├── StatusCards.tsx     ← Cards d'estat (inversió, cash, on track)
    │   │   ├── Allocation.tsx      ← Donut + llista d'actius
    │   │   ├── TopMovers.tsx       ← Top movers del dia
    │   │   └── Alerts.tsx          ← Alertes actives
    │   └── portfolio/
    │       └── PortfolioScreen.tsx ← Vista detallada de cartera
    └── test/
        └── setup.ts          ← Configuració global de tests (jest-dom, matchMedia mock)
```

---

## Design system — Liquid Glass

La UI segueix un disseny **mobile-first** (430px max-width) amb estètica *liquid glass*:

### Variables CSS (globals a `index.css`)

```css
:root {
  --bg-primary: #0a0a0f;
  --bg-secondary: #111118;
  --glass-bg: rgba(255, 255, 255, 0.05);
  --glass-border: rgba(255, 255, 255, 0.08);
  --glass-blur: blur(40px) saturate(1.8);
  --accent-blue: #3b82f6;
  --text-primary: rgba(255, 255, 255, 0.95);
  --text-secondary: rgba(255, 255, 255, 0.5);
}
```

### Tema clar/fosc

El tema es gestiona amb Zustand (`useTheme.ts`) aplicant la classe `dark` a `<html>`. Detecta automàticament la preferència del sistema (`prefers-color-scheme`) en la inicialització.

```typescript
import { useThemeStore } from './hooks/useTheme';
const { isDark, toggle } = useThemeStore();
```

---

## API — Fetch client

Tot el tràfic HTTP passa per `src/core/api.ts`:

```typescript
const BASE = import.meta.env.VITE_API_URL ?? '/api/v1';

export async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}
```

En Docker local, Vite proxeja `/api` → `http://backend:8000` (configurat a `vite.config.ts`).

---

## Dades — TanStack Query

### useNetWorth

```typescript
const { data, isLoading, isError } = useNetWorth();
// data: NetWorthSnapshot | undefined
```

- Endpoint: `GET /api/v1/portfolio/networth`
- Refresca cada 5 minuts (staleTime: 5 min)
- Retry automàtic en error

### useMarketPrices

```typescript
const { data } = useMarketPrices();
// data: AssetPrice[] | undefined
```

- Endpoint: `GET /api/v1/market/prices`
- Refresca cada 5 minuts

### Tipus importants

```typescript
// Helper: converteix strings Decimal del backend a number
export const n = (v: string | number | null | undefined): number =>
  v == null ? 0 : typeof v === 'number' ? v : parseFloat(v) || 0;

// Camps correctes (NON el que sembla: inv_value no existeix)
interface NetWorthSnapshot {
  total_net_worth: string | number;
  investment_portfolio_value: string | number;  // ← camp real del backend
  cash_and_bank_value: string | number;          // ← camp real del backend
  change_eur: string | number;
  change_pct: string | number;
  asset_snapshots: AssetSnapshot[];
}
```

> ⚠️ **Important**: FastAPI serialitza `Decimal` com a **strings JSON** (e.g., `"23862.98"`).
> Usa sempre el helper `n()` per convertir a `number` abans d'operar.

---

## Gràfics — SVG pur

Cap dependència externa de charting. Tots els gràfics són SVG natiu:

### PortfolioChart

Gràfic de línia amb animació de **morphing** (600ms, ease-in-out) en canviar les dades o el període:

- Area gradient sota la línia
- Animació via `requestAnimationFrame` + interpolació lineal de paths
- Cercle al punt final amb pulsació
- Grid lines horitzontals (5 nivells)
- Àrea clicable com a `<svg>` responsiu

```tsx
<PortfolioChart data={[10000, 10500, 11200]} width={390} height={180} />
```

### DonutChart

SVG donut amb `stroke-dasharray` per representar pesos d'actius. Colors definits a `ASSET_COLORS` a `types/index.ts`.

### GoalRing

Ring circular de progrés per a l'objectiu de compra d'habitatge.

---

## Tests

### Executar

```bash
make test-fe          # Executa tots els tests (vitest --run)
make check-fe         # Compila TypeScript (tsc --noEmit)
```

O directament:

```bash
docker compose exec frontend npm test
docker compose exec frontend npm run test:watch   # Mode watch
docker compose exec frontend npm run typecheck
```

### Configuració

- **`vite.config.ts`**: entorn `jsdom`, globals Vitest activats, setupFiles apunta a `src/test/setup.ts`
- **`src/test/setup.ts`**: importa `@testing-library/jest-dom` + mock global de `window.matchMedia`

### Mock de `window.matchMedia`

`useTheme.ts` crida `window.matchMedia` a nivell de **mòdul** (fora de hooks/components). Això significa que el mock cal fer-lo a `setup.ts`, no a `beforeEach`:

```typescript
// src/test/setup.ts
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false, media: query, onchange: null,
    addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn(),
  })),
});
```

### Mock de `requestAnimationFrame`

`PortfolioChart` usa `requestAnimationFrame` per al morphing. Al test cal mockejar-lo **sense** cridar el callback (evita bucle infinit):

```typescript
beforeEach(() => {
  vi.stubGlobal('requestAnimationFrame', (_cb: FrameRequestCallback) => 0);
  vi.stubGlobal('cancelAnimationFrame', (_id: number) => {});
});
```

### Assercions amb text nodes mixts

Elements amb fills mixtos (text + elements) com `<span>▲ +1.713,54 €</span>` no es troben amb `screen.getByText('▲')`. Usa `textContent`:

```typescript
expect(document.body.textContent).toContain('▲');
```

### Cobertura actual (Març 2026)

| Fitxer | Tests |
|--------|-------|
| `src/types/index.test.ts` | 10 |
| `src/components/ui/Card.test.tsx` | 5 |
| `src/components/ui/StatusDot.test.tsx` | 6 |
| `src/hooks/useTheme.test.ts` | 6 |
| `src/components/charts/PortfolioChart.test.tsx` | 7 |
| `src/features/dashboard/HeroValue.test.tsx` | 6 |
| `src/features/dashboard/TopMovers.test.tsx` | 7 |
| **Total** | **47** |

---

## Docker

El frontend corre dins Docker amb Vite en mode dev (hot module replacement actiu):

```yaml
# docker-compose.yml
frontend:
  build: ./frontend
  volumes:
    - ./frontend:/app          # Codi font (hot reload)
    - /app/node_modules        # node_modules del contenidor (NO sobresciure)
  ports:
    - "8080:5173"
```

> ⚠️ El volum anònim `/app/node_modules` és **essencial**. Sense ell, el mount de `./frontend` sobreescriuria els `node_modules` instal·lats al contenidor i Vite no arrancaria.

### `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
```

---

## Variables d'entorn

| Variable | Default | Descripció |
|----------|---------|------------|
| `VITE_API_URL` | `/api/v1` | Base URL de l'API (proxy Vite en dev) |

En producció, Nginx servirà els estàtics compilats (`npm run build`) i proxejarà `/api/` al backend. El `VITE_API_URL` no cal perquè el prefix per defecte `/api/v1` ja funciona.

---

## Afegir un nou mòdul (pantalla)

1. Crear `src/features/<nom>/` amb `<Nom>Screen.tsx`
2. Afegir la ruta a `App.tsx`:
   ```tsx
   <Route path="/nom" element={<NomScreen />} />
   ```
3. Afegir l'entrada al `<NavBar>` si és una pantalla principal
4. Crear el hook de dades a `src/hooks/use<Nom>.ts` si cal un nou endpoint
5. Afegir els tipus corresponents a `src/types/index.ts`

Cap fitxer de `core/` ni `App.tsx` hauria de requerir canvis estructurals.
