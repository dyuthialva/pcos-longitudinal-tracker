import React from 'react';

interface DataCompletenessProps {
  percentage: number;
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

export const DataCompleteness: React.FC<DataCompletenessProps> = ({
  percentage,
  showLabel = true,
  size = 'md',
}) => {
  const getColor = (pct: number) => {
    if (pct >= 80) return 'bg-emerald-600';
    if (pct >= 60) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="flex items-center gap-2">
      <div className={`flex-1 bg-slate-200 rounded-full overflow-hidden ${size === 'sm' ? 'h-1.5 min-w-[60px]' : 'h-2 min-w-[80px]'}`}>
        <div
          className={`h-full rounded-full transition-all duration-300 ${getColor(percentage)}`}
          style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-mono font-medium text-slate-700 whitespace-nowrap">
          {percentage}%
        </span>
      )}
    </div>
  );
};
