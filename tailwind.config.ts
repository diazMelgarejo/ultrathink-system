import type { Config } from "tailwindcss";

// Dark operator console design tokens.
// Sourced from src/styles/tokens.css — these are the Tailwind aliases.
const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Backgrounds (dense dark console)
        canvas: {
          DEFAULT: "rgb(8, 10, 14)",   // outermost page
          surface: "rgb(14, 17, 23)",  // panels
          raised: "rgb(20, 24, 33)",   // cards, rows
          inset: "rgb(5, 7, 11)",      // wells, code
        },
        // Borders + dividers
        line: {
          DEFAULT: "rgb(34, 40, 51)",
          strong: "rgb(56, 64, 80)",
        },
        // Foreground
        ink: {
          DEFAULT: "rgb(231, 235, 244)",
          muted: "rgb(146, 156, 175)",
          subtle: "rgb(99, 107, 124)",
        },
        // Status
        status: {
          ok: "rgb(94, 200, 138)",
          warn: "rgb(234, 179, 8)",
          err: "rgb(239, 78, 100)",
          info: "rgb(120, 162, 247)",
          gpu: "rgb(186, 134, 255)",
        },
        // Accent (action / primary)
        accent: {
          DEFAULT: "rgb(120, 162, 247)",
          hover: "rgb(149, 184, 255)",
          mute: "rgb(60, 80, 130)",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "monospace",
        ],
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
      },
      boxShadow: {
        raised: "0 1px 0 0 rgba(0,0,0,0.6) inset, 0 1px 1px rgba(0,0,0,0.3)",
      },
    },
  },
  plugins: [],
};

export default config;
