import { useQuery } from '@tanstack/react-query';

import { artifactApi } from '@/services/artifactApi';
import type { Artifact } from '@/types/api.types';

function Loading() {
  return <div className="border-2 border-line p-6 text-center font-mono text-xs text-sub">加载中…</div>;
}

export function ArtifactViewer({ runId, artifact }: { runId: string; artifact: Artifact }) {
  const url = artifactApi.url(runId, artifact.name);

  if (artifact.kind === 'report' || artifact.name.endsWith('.html')) {
    // 自包含报告：iframe sandbox（无 allow-same-origin → opaque 源，读不到主站）
    return (
      <iframe
        title={artifact.name}
        src={url}
        sandbox="allow-scripts"
        className="h-[72vh] w-full border-2 border-ink bg-white"
      />
    );
  }
  if (artifact.kind === 'image') {
    return <img src={url} alt={artifact.name} className="max-w-full border-2 border-ink" />;
  }
  if (artifact.kind === 'csv') {
    return <CsvView runId={runId} name={artifact.name} />;
  }
  return <TextView runId={runId} name={artifact.name} />;
}

function CsvView({ runId, name }: { runId: string; name: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['csv', runId, name],
    queryFn: () => artifactApi.csvPreview(runId, name),
  });
  if (isLoading) return <Loading />;
  if (isError || !data) return <div className="border-2 border-ink bg-coral p-4 text-white">CSV 读取失败</div>;
  return (
    <div className="border-2 border-ink">
      <div className="max-h-[72vh] overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr>
              {data.columns.map((c, i) => (
                <th
                  key={i}
                  className="sticky top-0 whitespace-nowrap border-b-2 border-ink bg-panel px-3 py-2 text-left font-mono text-[11px] font-bold uppercase tracking-wide text-sub"
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, i) => (
              <tr key={i} className="hover:bg-lime/10">
                {row.map((cell, j) => (
                  <td key={j} className="border-b border-line px-3 py-2 align-top">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="border-t-2 border-ink bg-panel px-3 py-2 font-mono text-[11px] text-sub">
        共 {data.total} 行{data.truncated ? ` · 仅显示前 ${data.rows.length}` : ''}
      </div>
    </div>
  );
}

function TextView({ runId, name }: { runId: string; name: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['text', runId, name],
    queryFn: () => artifactApi.text(runId, name),
  });
  if (isLoading) return <Loading />;
  if (isError) return <div className="border-2 border-ink bg-coral p-4 text-white">读取失败</div>;
  return (
    <pre className="max-h-[72vh] w-full overflow-auto whitespace-pre-wrap break-words border-2 border-ink bg-ink p-3 font-mono text-xs leading-relaxed text-paper">
      {data}
    </pre>
  );
}
