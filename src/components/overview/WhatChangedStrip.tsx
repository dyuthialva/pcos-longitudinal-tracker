import { type FC } from 'react';
import type { ClinicalDelta, Visit } from '../../types/clinical';
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';

interface WhatChangedStripProps {
  visit: Visit;
  onSelectDomain: (domain: string) => void;
}

function rankDelta(delta: ClinicalDelta): number {
  if (delta.statusSeverity === 'high') return 3;
  if (delta.statusSeverity === 'moderate') return 2;
  const magnitude = Math.abs(delta.numericDelta ?? 0);
  return magnitude > 0 ? 1 : 0;
}

export const WhatChangedStrip: FC<WhatChangedStripProps> = ({ visit, onSelectDomain }) => {
  const top = [...visit.deltas]
    .filter((d) => d.isMeaningful)
    .sort((a, b) => rankDelta(b) - rankDelta(a) || Math.abs(b.numericDelta ?? 0) - Math.abs(a.numericDelta ?? 0))
    .slice(0, 3);

  if (top.length === 0) return null;

  return (
    <section className="bg-white border border-slate-200 rounded-lg p-4 shadow-xs">
      <div className="flex items-center justify-between gap-2 mb-3">
        <h3 className="text-sm font-semibold text-slate-900 m-0">What changed most</h3>
        <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400">
          Meaningful deltas only
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {top.map((delta) => {
          const Icon =
            delta.direction === 'up' ? ArrowUpRight : delta.direction === 'down' ? ArrowDownRight : Minus;
          return (
            <button
              key={delta.id}
              type="button"
              onClick={() => onSelectDomain(delta.domain)}
              className="text-left rounded-md border border-slate-200 bg-slate-50/80 hover:bg-slate-100 px-3 py-2"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-[11px] font-medium text-slate-500">{delta.domain}</span>
                <Icon className="w-3.5 h-3.5 text-slate-500" />
              </div>
              <p className="text-xs font-semibold text-slate-900 mt-1 m-0">{delta.parameter}</p>
              <p className="text-[11px] font-mono text-slate-600 mt-0.5 m-0">{delta.deltaDisplay}</p>
            </button>
          );
        })}
      </div>
    </section>
  );
};
