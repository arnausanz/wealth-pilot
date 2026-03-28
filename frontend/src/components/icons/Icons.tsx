interface IconProps {
  color: string;
  size?: number;
}

export function SunIcon({ color, size = 18 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
      <circle cx="10" cy="10" r="3.5" />
      <line x1="10" y1="1.5" x2="10" y2="3.5" />
      <line x1="10" y1="16.5" x2="10" y2="18.5" />
      <line x1="1.5" y1="10" x2="3.5" y2="10" />
      <line x1="16.5" y1="10" x2="18.5" y2="10" />
      <line x1="3.93" y1="3.93" x2="5.35" y2="5.35" />
      <line x1="14.65" y1="14.65" x2="16.07" y2="16.07" />
      <line x1="3.93" y1="16.07" x2="5.35" y2="14.65" />
      <line x1="14.65" y1="5.35" x2="16.07" y2="3.93" />
    </svg>
  );
}

export function MoonIcon({ color, size = 18 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 10.9A7 7 0 1 1 9.1 3a5.5 5.5 0 0 0 7.9 7.9Z" />
    </svg>
  );
}

// ── Nav icons ────────────────────────────────────────────────────────────────

export function HomeIcon({ color, size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      {/* House outline with door — single clean path */}
      <path d="M3 9.5L10 3l7 6.5V17.5H13V12.5H7V17.5H3V9.5Z" />
    </svg>
  );
}

export function PortfolioIcon({ color, size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      {/* Briefcase — body + handle + shelf */}
      <rect x="2" y="7" width="16" height="11" rx="2" />
      <path d="M7 7V5.5A1.5 1.5 0 0 1 8.5 4h3A1.5 1.5 0 0 1 13 5.5V7" />
      <line x1="2" y1="12" x2="18" y2="12" />
    </svg>
  );
}

export function ChartIcon({ color, size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      {/* Upward trend line with top-right arrow */}
      <polyline points="2,16 6,10.5 10,12.5 17,4" />
      <polyline points="13.5,4 17,4 17,7.5" />
    </svg>
  );
}

export function AnalyticsIcon({ color, size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      {/* Three ascending bar columns */}
      <rect x="2.5" y="11" width="4" height="7" rx="1" />
      <rect x="8" y="7" width="4" height="11" rx="1" />
      <rect x="13.5" y="3" width="4" height="15" rx="1" />
    </svg>
  );
}

export function ListIcon({ color, size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
      {/* Clean list — three horizontal lines, last one shorter */}
      <line x1="3.5" y1="5.5" x2="16.5" y2="5.5" />
      <line x1="3.5" y1="10" x2="16.5" y2="10" />
      <line x1="3.5" y1="14.5" x2="11.5" y2="14.5" />
    </svg>
  );
}

export function GearIcon({ color, size = 20 }: IconProps) {
  return (
    // Uses 24×24 viewBox — Heroicons cog-6-tooth (mathematically precise)
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
      <path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  );
}

export function WarningIcon({ color, size = 16 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495Z" />
      <line x1="10" y1="8" x2="10" y2="11.5" />
      <circle cx="10" cy="14" r="0.6" fill={color} stroke="none" />
    </svg>
  );
}
