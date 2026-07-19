/**
 * Design tokens (reference palette from the dataviz method, both modes
 * validated). Canvas can't read CSS custom properties cheaply per frame,
 * so the same values live here for draw code and in styles.css for DOM.
 * Series colors: home = categorical slot 1 (blue), away = slot 2 (green),
 * assigned in fixed order.
 */

export interface ThemePalette {
  surface: string;
  page: string;
  inkPrimary: string;
  inkSecondary: string;
  inkMuted: string;
  gridline: string;
  baseline: string;
  home: string;
  away: string;
  /** Rink markings — map features, kept recessive next to the data dots. */
  rinkLineRed: string;
  rinkLineBlue: string;
  creaseFill: string;
}

export const LIGHT: ThemePalette = {
  surface: "#fcfcfb",
  page: "#f9f9f7",
  inkPrimary: "#0b0b0b",
  inkSecondary: "#52514e",
  inkMuted: "#898781",
  gridline: "#e1e0d9",
  baseline: "#c3c2b7",
  home: "#2a78d6",
  away: "#008300",
  rinkLineRed: "rgba(211, 69, 68, 0.45)",
  rinkLineBlue: "rgba(42, 120, 214, 0.35)",
  creaseFill: "rgba(42, 120, 214, 0.10)",
};

export const DARK: ThemePalette = {
  surface: "#1a1a19",
  page: "#0d0d0d",
  inkPrimary: "#ffffff",
  inkSecondary: "#c3c2b7",
  inkMuted: "#898781",
  gridline: "#2c2c2a",
  baseline: "#383835",
  home: "#3987e5",
  away: "#008300",
  rinkLineRed: "rgba(230, 103, 103, 0.45)",
  rinkLineBlue: "rgba(57, 135, 229, 0.40)",
  creaseFill: "rgba(57, 135, 229, 0.14)",
};

export function paletteFor(dark: boolean): ThemePalette {
  return dark ? DARK : LIGHT;
}
