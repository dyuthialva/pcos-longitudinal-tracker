export function LoadingSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3" aria-busy="true" aria-live="polite">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-16 rounded-lg border border-slate-200 bg-slate-100 animate-pulse" />
      ))}
    </div>
  );
}
