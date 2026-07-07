import { Route, Routes } from 'react-router-dom';

import { ActiveRunsDock } from '@/components/ActiveRunsDock';
import ConsolePage from '@/pages/console/ConsolePage';
import RunDetailPage from '@/pages/runs/RunDetailPage';
import RunsPage from '@/pages/runs/RunsPage';

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<ConsolePage />} />
        <Route path="/runs" element={<RunsPage />} />
        <Route path="/runs/:runId" element={<RunDetailPage />} />
      </Routes>
      <ActiveRunsDock />
    </>
  );
}
