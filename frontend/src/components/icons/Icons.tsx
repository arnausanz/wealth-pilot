interface IconProps {
  color: string;
  size?: number;
}

export function SunIcon({ color, size = 18 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 18 18"
      fill="none"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
    >
      <circle cx="9" cy="9" r="3.5" />
      <line x1="9" y1="1.5" x2="9" y2="3" />
      <line x1="9" y1="15" x2="9" y2="16.5" />
      <line x1="2.64" y1="2.64" x2="3.7" y2="3.7" />
      <line x1="14.3" y1="14.3" x2="15.36" y2="15.36" />
      <line x1="1.5" y1="9" x2="3" y2="9" />
      <line x1="15" y1="9" x2="16.5" y2="9" />
      <line x1="2.64" y1="15.36" x2="3.7" y2="14.3" />
      <line x1="14.3" y1="3.7" x2="15.36" y2="2.64" />
    </svg>
  );
}

export function MoonIcon({ color, size = 18 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 18 18"
      fill="none"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M15.5 9.7A6.5 6.5 0 1 1 8.3 2.5a5 5 0 0 0 7.2 7.2Z" />
    </svg>
  );
}

export function HomeIcon({ color, size = 20 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 7.5 10 2l7 5.5V16a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 3 16V7.5Z" />
      <path d="M7.5 17.5V11h5v6.5" />
    </svg>
  );
}

export function PortfolioIcon({ color, size = 20 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="2" y="4" width="16" height="12" rx="2" />
      <path d="M2 9h16" />
      <circle cx="10" cy="12.5" r="1.5" />
    </svg>
  );
}

export function ChartIcon({ color, size = 20 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="3,14 7,9 11,11 17,4" />
      <polyline points="13,4 17,4 17,8" />
    </svg>
  );
}

export function ListIcon({ color, size = 20 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
    >
      <line x1="3" y1="5" x2="17" y2="5" />
      <line x1="3" y1="10" x2="17" y2="10" />
      <line x1="3" y1="15" x2="12" y2="15" />
    </svg>
  );
}

export function GearIcon({ color, size = 20 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="10" cy="10" r="2.5" />
      <path d="M16.2 12.5a1.2 1.2 0 0 0 .2 1.3l.04.04a1.45 1.45 0 1 1-2.05 2.05l-.04-.04a1.2 1.2 0 0 0-1.3-.2 1.2 1.2 0 0 0-.73 1.1v.12a1.45 1.45 0 0 1-2.9 0v-.06a1.2 1.2 0 0 0-.79-1.1 1.2 1.2 0 0 0-1.3.2l-.04.04a1.45 1.45 0 1 1-2.05-2.05l.04-.04a1.2 1.2 0 0 0 .2-1.3 1.2 1.2 0 0 0-1.1-.73H4.15a1.45 1.45 0 0 1 0-2.9h.06a1.2 1.2 0 0 0 1.1-.79 1.2 1.2 0 0 0-.2-1.3l-.04-.04A1.45 1.45 0 1 1 7.12 5.1l.04.04a1.2 1.2 0 0 0 1.3.2h.06a1.2 1.2 0 0 0 .73-1.1V4.15a1.45 1.45 0 0 1 2.9 0v.06a1.2 1.2 0 0 0 .73 1.1 1.2 1.2 0 0 0 1.3-.2l.04-.04a1.45 1.45 0 1 1 2.05 2.05l-.04.04a1.2 1.2 0 0 0-.2 1.3v.06a1.2 1.2 0 0 0 1.1.73h.12a1.45 1.45 0 0 1 0 2.9h-.06a1.2 1.2 0 0 0-1.1.73Z" />
    </svg>
  );
}

export function AnalyticsIcon({ color, size = 20 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="10" width="3.5" height="7" rx="0.5" />
      <rect x="8.25" y="6" width="3.5" height="11" rx="0.5" />
      <rect x="13.5" y="3" width="3.5" height="14" rx="0.5" />
    </svg>
  );
}

export function WarningIcon({ color, size = 16 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M6.86 2.57 1.21 12a1.33 1.33 0 0 0 1.14 2h11.3a1.33 1.33 0 0 0 1.14-2L9.14 2.57a1.33 1.33 0 0 0-2.28 0Z" />
      <line x1="8" y1="6" x2="8" y2="9" />
      <circle cx="8" cy="11.5" r="0.5" fill={color} />
    </svg>
  );
}
