import type { CSSProperties } from "react";

export interface ThemeData {
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  background_color?: string;
  text_color?: string;
  font_heading?: string;
  font_body?: string;
  mood?: string;
}

export interface ResolvedTheme {
  bg: string;
  text: string;
  pri: string;
  sec: string;
  acc: string;
  hFont: string;
  bFont: string;
}

export function normalizeFontName(fontName?: string): string {
  const raw = (fontName || "").trim();
  if (!raw) return "Inter";
  return raw.replace(/^['"]+|['"]+$/g, "").replace(/\s+/g, " ").trim();
}

export function resolveTheme(t: ThemeData | null | undefined): ResolvedTheme {
  const th = t ?? {};
  const headingName = normalizeFontName(th.font_heading);
  const bodyName = normalizeFontName(th.font_body);
  return {
    bg: th.background_color || th.primary_color || "#0f172a",
    text: th.text_color || "#f1f5f9",
    pri: th.primary_color || "#6366f1",
    sec: th.secondary_color || "#312e81",
    acc: th.accent_color || "#f59e0b",
    hFont: `'${headingName}', sans-serif`,
    bFont: `'${bodyName}', sans-serif`,
  };
}

export function themeVars(c: ResolvedTheme): CSSProperties {
  return {
    "--s-bg": c.bg,
    "--s-text": c.text,
    "--s-pri": c.pri,
    "--s-sec": c.sec,
    "--s-acc": c.acc,
    "--s-hfont": c.hFont,
    "--s-bfont": c.bFont,
  } as CSSProperties;
}

/**
 * Build a single Google Fonts URL for multiple font families with full weight range.
 * Deduplicates and skips empty/default names.
 */
export function buildGoogleFontsUrl(fontNames: string[]): string {
  const unique = Array.from(
    new Set(
      fontNames
        .map((f) => normalizeFontName(f))
        .filter((f) => f && f !== "Inter")
    )
  );
  // Always include Inter as base fallback
  unique.push("Inter");
  const families = unique
    .map((f) => `family=${f.replace(/\s+/g, "+")}:wght@400;500;600;700;800;900`)
    .join("&");
  return `https://fonts.googleapis.com/css2?${families}&display=swap`;
}
