/** 扁平风(flat-pop) design token：纸底点阵 + 撞色实心 + 超粗描边 + 硬偏移投影 + back-out 弹性。零 emoji。 */
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#f3f1ea',
        panel: '#ffffff',
        ink: '#141414',
        sub: '#4a4a4a',
        line: '#e4e0d3',
        blue: '#2450e6',
        coral: '#ff4d4d',
        lime: '#c7f03a',
        yellow: '#ffd12e',
        cyan: '#22c6e0',
        violet: '#7b3ff2',
      },
      fontFamily: {
        // 展示字（海报巨字 / 数字块 / 标题）——重量级 grotesk
        grot: ['"Helvetica Neue"', '"Arial Black"', 'system-ui', '-apple-system', '"PingFang SC"', 'sans-serif'],
        sans: ['system-ui', '-apple-system', '"PingFang SC"', '"Segoe UI"', 'sans-serif'],
        mono: ['"SF Mono"', 'ui-monospace', 'Menlo', 'monospace'],
      },
      boxShadow: {
        pop: '5px 5px 0 #141414',
        'pop-sm': '3px 3px 0 #141414',
        'pop-lg': '8px 8px 0 #141414',
        'pop-xl': '11px 11px 0 #141414',
      },
      transitionTimingFunction: {
        pop: 'cubic-bezier(0.34,1.56,0.64,1)',
        back: 'cubic-bezier(0.34,1.56,0.64,1)',
        tap: 'cubic-bezier(0.3,0.9,0.4,1)',
      },
      keyframes: {
        reveal: { '0%': { opacity: '0', transform: 'translateY(14px)' }, '100%': { opacity: '1', transform: 'none' } },
        floaty: { '0%,100%': { transform: 'translateY(0) rotate(-6deg)' }, '50%': { transform: 'translateY(-10px) rotate(-1deg)' } },
        wobble: { '0%,100%': { transform: 'rotate(-3deg)' }, '50%': { transform: 'rotate(4deg)' } },
        bpulse: { '0%,100%': { transform: 'scale(1)' }, '50%': { transform: 'scale(1.5)' } },
        spinslow: { to: { transform: 'rotate(360deg)' } },
      },
      animation: {
        floaty: 'floaty 5s ease-in-out infinite',
        wobble: 'wobble 6s ease-in-out infinite',
        bpulse: 'bpulse 1.6s cubic-bezier(0.34,1.56,0.64,1) infinite',
        spinslow: 'spinslow 14s linear infinite',
      },
    },
  },
  plugins: [],
};
