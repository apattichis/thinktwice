/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Base backgrounds
        'base': '#09090B',
        'card': '#18181B',
        'elevated': '#27272A',
        'border': '#3F3F46',

        // Text colors
        'primary': '#FAFAFA',
        'secondary': '#A1A1AA',
        'muted': '#71717A',

        // Step colors
        'step-draft': '#3B82F6',
        'step-critique': '#F59E0B',
        'step-verify': '#8B5CF6',
        'step-refine': '#10B981',

        // Verdict colors
        'verdict-verified': '#10B981',
        'verdict-refuted': '#EF4444',
        'verdict-unclear': '#F59E0B',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
