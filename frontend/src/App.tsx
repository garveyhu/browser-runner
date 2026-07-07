import { Route, Routes } from 'react-router-dom';

import ConsolePage from '@/pages/console/ConsolePage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ConsolePage />} />
      {/* 运行历史 / 详情 —— P3 换真页 */}
      <Route path="/runs" element={<div className="p-10 font-mono text-sub">运行历史（P3 建设中）</div>} />
    </Routes>
  );
}
