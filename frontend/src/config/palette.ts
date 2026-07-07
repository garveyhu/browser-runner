// 卡片图标 tile 配色按 index 轮转（撞色 pop）。
export const TILE_COLORS = ['blue', 'coral', 'violet', 'lime', 'cyan'] as const;
export type TileColor = (typeof TILE_COLORS)[number];

export const tileColor = (i: number): TileColor => TILE_COLORS[i % TILE_COLORS.length];

// 浅底（lime/cyan）glyph 用墨色，深底（blue/coral/violet）用白
export const tileGlyphIsInk = (c: TileColor): boolean => c === 'lime' || c === 'cyan';

export const TILE_BG: Record<TileColor, string> = {
  blue: 'bg-blue',
  coral: 'bg-coral',
  violet: 'bg-violet',
  lime: 'bg-lime',
  cyan: 'bg-cyan',
};
