import React from 'react';
import type { DomainScore } from '../../types/clinical';
import { AttentionBadge } from '../common/Badge';
import { ChevronRight, HelpCircle } from 'lucide-react';


interface AttentionDomainProps {
  scoreData: DomainScore;
  onClick: () => void;
}

export const AttentionDomain: React.FC<AttentionDomainProps> = ({ scoreData, onClick }) => {
  const { domain, score, band, isInsufficientData, insufficientReason, contributingParameters } = scoreData;

  const getBarColor = (val: number | null) => {
    if (val === null) return 'bg-slate-300';
    if (val < 40) return 'bg-emerald-500';
    if (val < 65) return 'bg-amber-500';
    if (val < 80) return 'bg-orange-500';
    return 'bg-rose-600';
  };

  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      className={`group w-full p-4 rounded-lg border transition-all text-left cursor-pointer focus:outline-none focus:ring-2 focus:ring-teal-600 ${
        isInsufficientData
          ? 'bg-slate-50/80 border-dashed border-slate-300 hover:border-slate-400 hover:bg-slate-100/70'
          : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-2xs'
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Domain name & details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-900 group-hover:text-teal-900 transition">
              {domain}
            </h4>
            <AttentionBadge band={band} size="sm" />
          </div>

          {isInsufficientData ? (
            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5 leading-relaxed">
              <HelpCircle className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span>{insufficientReason || 'Not enough validated observations are available for this domain.'}</span>
            </p>
          ) : (
            <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
              <span className="truncate">
                Key markers: {contributingParameters.slice(0, 3).join(', ')}
                {contributingParameters.length > 3 && ` +${contributingParameters.length - 3}`}
              </span>
            </div>
          )}
        </div>

        {/* Score & Progress Bar */}
        <div className="flex items-center gap-4 sm:w-64 shrink-0 justify-between sm:justify-end">
          {isInsufficientData ? (
            <div className="text-xs font-mono text-slate-400 italic">
              Score N/A
            </div>
          ) : (
            <div className="w-full sm:w-48 space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">
                  Score
                </span>
                <span className="font-bold text-slate-900">
                  {score} <span className="text-slate-400 font-normal">/ 100</span>
                </span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200/60">
                <div
                  className={`h-full rounded-full transition-all duration-300 attention-bar ${getBarColor(score)}`}
                  style={{ width: `${score ?? 0}%` }}
                  aria-label={`${domain} attention score ${score} of 100, band ${band}`}
                />
              </div>
            </div>
          )}

          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-teal-700 group-hover:translate-x-0.5 transition shrink-0" />
        </div>
      </div>
    </div>
  );
};
