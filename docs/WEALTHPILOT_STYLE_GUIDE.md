# WealthPilot Design System v1
## Fonts
Body: `'SF Pro Text', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif`
Display (títols): `'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif`
Números/dades: `'SF Pro Rounded', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif`
Mai monospace. Mai serif. La font del sistema iOS és la base.
### Escala tipogràfica
- Hero value (patrimoni total): 38px, weight 300, letter-spacing -0.03em, font números
- Títol pantalla: 24px, weight 700, letter-spacing -0.02em, font display
- Valor KPI dins card: 22px, weight 600, font números
- Nom actiu / element llista: 13px, weight 500, font body
- Dada secundària: 12px, weight 400, font números
- Label secció (caps): 11px, weight 600, letter-spacing 0.06em, uppercase, color textTertiary, font números
- Subtítol / meta: 10-11px, font body
- Micro label: 9px, weight 600, letter-spacing 0.04em, font números
Regla: letter-spacing mai >0.08em. Labels a 0.04-0.06em. Títols a -0.02em. Números grans a -0.03em.

## Paleta de colors
Dos temes (dark/light), selecció automàtica via `prefers-color-scheme`. Toggle manual disponible.
### Dark
```
bg: #0B0F19
glassBg: rgba(255,255,255,0.05)
glassBorder: rgba(255,255,255,0.08)
border: rgba(255,255,255,0.06)
text: #F1F5F9
textSecondary: rgba(255,255,255,0.55)
textTertiary: rgba(255,255,255,0.25)
accent: #3B82F6
positive: #34D399
negative: #FB7185
warning: #FBBF24
cardShadow: 0 2px 8px rgba(0,0,0,0.2), 0 0 1px rgba(255,255,255,0.05) inset
navBg: rgba(11,15,25,0.75)
```
### Light
```
bg: #F2F4F8
glassBg: rgba(255,255,255,0.5)
glassBorder: rgba(255,255,255,0.7)
border: rgba(0,0,0,0.05)
text: #0F172A
textSecondary: rgba(0,0,0,0.5)
textTertiary: rgba(0,0,0,0.25)
accent: #2563EB
positive: #059669
negative: #DC2626
warning: #D97706
cardShadow: 0 2px 12px rgba(0,0,0,0.04), 0 0 1px rgba(255,255,255,0.8) inset
navBg: rgba(242,244,248,0.75)
```
Colors per actiu (fixes, no canvien entre temes):
MSCI World=#3B82F6, Or=#F59E0B, Europe=#8B5CF6, EM=#06B6D4, Japó=#10B981, Defensa=#F97316, BTC=#E11D48, Efectiu=textTertiary

## Liquid Glass
Totes les superfícies (cards, inputs, nav, selectors) usen fons semi-transparent + backdrop-filter.
```
backdrop-filter: blur(40px) saturate(1.8)
-webkit-backdrop-filter: blur(40px) saturate(1.8)
```
Fons de card: `glassBg`. Border: `glassBorder`. Mai fons opac sòlid per cards/contenidors.
Excepció: el `bg` de pàgina sí és opac.
El shadow inset (`0 0 1px rgba(...) inset`) dóna la vora interior brillant característica del vidre.

## Cards i layout
- Max width app: 430px, centrat
- Padding horitzontal general: 24px
- Gap entre seccions verticals: 20px (padding-top de cada secció)
- Border-radius cards: 16px (o 14px per cards petites dins grid)
- Padding intern card: 14-18px
- Grid 2 columnes per KPI cards (gap 10px)
- Grid 3 columnes per quick actions (gap 8px)
- Llistes verticals: gap 1px entre elements, primer element radius top 14px, últim radius bottom 14px, intermedis 2px → efecte llista unificada
- Cada peça d'informació viu dins la seva card independent. No barrejar conceptes dins una mateixa card.
- Jerarquia visual: label caps petit → valor gran → subtítol/context petit

## Iconografia
SVG stroke-based, estil SF Symbols / Lucide. Característiques:
- stroke-width: 1.5
- stroke-linecap: round
- stroke-linejoin: round
- fill: none (sempre contorn, mai ple)
- Mida: 18-20px viewBox
- Color dinàmic via prop (accent per actiu, textTertiary per inactiu)
- Per representar actius en llistes: quadrat 32x32 amb borderRadius 10, fons `${color}15`, text 2 lletres del ticker (11px, weight 700, font números, color del actiu)
Zero emojis a tota la UI. Tot icono és SVG inline.

## Gràfics
### Línia temporal (evolució patrimoni, net worth, etc.)
- SVG inline, viewBox proporcional (ex: 343×160)
- Corba bézier suau (cubic bezier entre punts, control points a 1/3 distància)
- Gradient fill sota la línia: color accent amb opacity 0.2→0.0 vertical
- Línia: stroke-width 2, stroke-linecap round
- Punt final: cercle r=3.5 amb halo pulsant (animate r 6→11→6, opacity 0.2→0.04→0.2, dur 2.5s)
- Grid lines: dashed (2 4), color border, amb label €Xk a la dreta
- Color línia: positive si puja, negative si baixa
### Transició entre temporalitats (MORPHING)
Totes les sèries tenen el MATEIX nombre de punts (ex: 60). Quan canvia el rang:
1. Guardar sèrie actual com `fromData`
2. Calcular nova sèrie `toData`
3. Interpolar punt per punt: `from[i] + (to[i] - from[i]) * ease(t)` durant 600ms
4. Easing: cubic ease-in-out `t < 0.5 ? 4t³ : 1 - (-2t+2)³/2`
La línia MAI desapareix. Sempre fluctua d'una forma a l'altra.
### Donut chart (distribució cartera)
- SVG arcs amb stroke (no fill), stroke-width 14
- Hover: stroke-width +4, altres segments opacity 0.4, transició 0.3s
- Centre: label "TOTAL" + valor, o nom segment + % en hover
- Gap entre segments: 1° d'arc
### Anell de progrés (objectius)
- SVG cercle amb stroke-dasharray/dashoffset
- Animació d'entrada amb transition stroke-dashoffset 1s ease
- Text central: percentatge (weight 600) + subtítol meta

## Selector de temporalitat
Barra horitzontal amb botons: 1M, 3M, 6M, 1A, Tot, Custom.
- Contenidor: glassBg + glassBlur, borderRadius 12, padding 3
- Botó actiu: fons accent amb opacity 0.12-0.2, color accent
- Botó inactiu: transparent, color textTertiary
- Font: 12px, weight 600, font números
- "Custom" desplega 2 date inputs amb animació slideDown (0.3s ease, translateY -8→0 + opacity 0→1)

## Animacions i transicions
- Tema dark↔light: transition background 0.4s ease, color 0.4s ease al contenidor principal
- Hover buttons: opacity 0.85
- Active buttons: transform scale(0.97)
- Card hover: no canvi (mòbil-first, no hover states elaborats)
- Gràfic morphing: 600ms cubic ease-in-out
- Donut hover: stroke-width transició 0.3s ease
- Aparició elements (modals, custom picker): slideDown 0.3s ease
- Progress ring: stroke-dashoffset 1s ease
- Pulsació punt gràfic: SVG animate 2.5s infinite
Principi: transicions ràpides (0.2-0.4s) per micro-interaccions, 0.6s per canvis de dades, 1s per progress.

## Nav bar inferior
- Fixed bottom, maxWidth 430, centrat
- Glass: navBg + glassBlur
- Border top: glassBorder
- Padding: 8px 0 20px (safe area iOS)
- 5 ítems: icona SVG 20px + label 9px
- Actiu: color accent, weight 600
- Inactiu: color textTertiary, weight 400

## Status bar
Simulada amb hora 9:41 + icones bateria/senyal SVG. Color textSecondary. Padding 14px 24px.

## Alertes
Card amb fons `${colorAlerta}10`, border `${colorAlerta}25`, borderRadius 16. Icona SVG warning + label caps + text descriptiu.

## Formularis i inputs
- Background: glassBg
- Border: glassBorder
- Border-radius: 10px
- Padding: 8-10px
- Font: 12px, font números
- Labels: 9px, caps, letter-spacing 0.06em, color textTertiary
- Grups de 2: grid 2 columnes, gap 8px

## Principis generals
1. Mobile-first (430px max). Tot ha de funcionar bé en pantalla mòbil.
2. Informació jeràrquica: el número important gran, el context petit.
3. Una card = un concepte. Mai barrejar informacions no relacionades.
4. Glass everywhere: cap superfície opaca excepte el fons de pàgina.
5. Coherència iOS: comportament, gestos i estètica nativa Apple.
6. Dades numèriques sempre amb font números (SF Pro Rounded).
7. Semàfors: green=positive, yellow=warning, red=negative. Punt lluminós 8px amb box-shadow glow.
8. Zero decoració innecessària. Si no aporta informació, no hi és.
