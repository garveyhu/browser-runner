import type { CSSProperties } from 'react';

/** 错峰弹入延迟：给 `.reveal` 元素传 --i。CSS 自定义属性需 cast。 */
export const revealDelay = (i: number): CSSProperties => ({ ['--i']: i }) as CSSProperties;
