// 命名 SVG 图标库（thick-outline · stroke=currentColor 适配彩色 tile）。零 emoji：
// 查不到的名字回落到通用四角星，绝不返 emoji。

const PATHS: Record<string, string> = {
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5l4.5 4.5"/>',
  form:
    '<rect x="5" y="3.5" width="14" height="17" rx="2"/><path d="M9 3.5V2.5h6v1"/><path d="M8.5 9h7M8.5 13h7M8.5 17h4"/>',
  rocket:
    '<path d="M12 3c3.5 2.5 5 6.5 4 11l-4-2.5L8 14c-1-4.5.5-8.5 4-11z"/><path d="M8.5 14l-3 2 1.5 3M15.5 14l3 2-1.5 3"/><circle cx="12" cy="9" r="1.6"/>',
  publish: '<path d="M21 3L10 14"/><path d="M21 3l-7 18-4-8-8-4z"/>',
  pulse: '<path d="M3 12h4l2.5-7 4 14 2.5-9 1.5 2h3.5"/>',
  globe:
    '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.5 2.4 2.5 14.6 0 17M12 3.5c-2.5 2.4-2.5 14.6 0 17"/>',
  download: '<path d="M12 3v11"/><path d="M7.5 10L12 14.5 16.5 10"/><path d="M4.5 19.5h15"/>',
  upload: '<path d="M12 14.5v-11"/><path d="M7.5 8L12 3.5 16.5 8"/><path d="M4.5 19.5h15"/>',
  link:
    '<path d="M9.5 14.5l5-5"/><path d="M8 12l-2 2a3.5 3.5 0 005 5l2-2"/><path d="M16 12l2-2a3.5 3.5 0 00-5-5l-2 2"/>',
  grid:
    '<rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.5"/>',
  eye: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
  layers: '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
  tag: '<path d="M4 4h7l9 9-7 7-9-9z"/><circle cx="8.5" cy="8.5" r="1.6"/>',
  gear:
    '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
  bolt: '<path d="M13 2L4 14h6l-1 8 9-12h-6z"/>',
  camera:
    '<rect x="3" y="6.5" width="18" height="13" rx="2.5"/><circle cx="12" cy="13" r="3.5"/><path d="M8.5 6.5l1.5-2.5h4l1.5 2.5"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3.5 2"/>',
};

const DEFAULT_PATH =
  '<path d="M12 2.5l2.6 6.9 6.9 2.6-6.9 2.6L12 21.5l-2.6-6.9L2.5 12l6.9-2.6z"/>';

interface IconProps {
  name: string;
  className?: string;
  size?: number;
}

export function Icon({ name, className, size = 24 }: IconProps) {
  const inner = PATHS[name] ?? DEFAULT_PATH;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
      dangerouslySetInnerHTML={{ __html: inner }}
    />
  );
}
