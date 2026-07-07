/** 扁平风(flat-pop) design token：纸底 + 撞色 + 粗描边 + 硬偏移投影 + back-out 弹性缓动。零 emoji。 */
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#f3f1ea',
        panel: '#fffdf7',
        ink: '#141414',
        sub: '#6b6459',
        line: '#e4e0d3',
        blue: '#2450e6',
        coral: '#ff4d4d',
        lime: '#c7f03a',
        sun: '#ffd12e',
        cyan: '#22c6e0',
        violet: '#7b3ff2',
      },
      fontFamily: {
        sans: ['"PingFang SC"', '"Hiragino Sans GB"', '"Microsoft YaHei"', '-apple-system', 'sans-serif'],
        mono: ['"SF Mono"', '"JetBrains Mono"', 'ui-monospace', 'Menlo', 'monospace'],
      },
      boxShadow: {
        pop: '5px 5px 0 #141414',
        'pop-sm': '3px 3px 0 #141414',
        'pop-lg': '8px 8px 0 #141414',
      },
      transitionTimingFunction: {
        back: 'cubic-bezier(0.34,1.56,0.64,1)',
      },
      keyframes: {
        reveal: { '0%': { opacity: '0', transform: 'translateY(14px)' }, '100%': { opacity: '1', transform: 'none' } },
        spin: { to: { transform: 'rotate(360deg)' } },
      },
      animation: {
        reveal: 'reveal .5s cubic-bezier(0.34,1.56,0.64,1) both',
      },
    },
  },
  plugins: [],
};
