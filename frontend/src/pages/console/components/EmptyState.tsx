export function EmptyState() {
  return (
    <div className="border-[2.5px] border-dashed border-ink bg-panel p-10 text-center shadow-pop">
      <h2 className="text-2xl font-black">还没有流程</h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-sub">
        复制模板开一个 —— registry 自动收录、控制台自动渲染、CLI 自动可跑，内核一行不动。
      </p>
      <code className="mt-4 inline-block border-2 border-ink bg-paper px-3 py-1.5 font-mono text-xs">
        cp -r flows/_template flows/&lt;你的流程名&gt;
      </code>
    </div>
  );
}
