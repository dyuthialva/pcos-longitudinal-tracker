import React from 'react';
import { Info } from 'lucide-react';


export const DisclaimerBanner: React.FC = () => {
  return (
    <div className="bg-slate-100/90 border-b border-slate-200 px-4 py-2.5 sm:px-6">
      <div className="max-w-7xl mx-auto flex items-start sm:items-center gap-3">
        <div className="p-1 rounded bg-slate-200 text-slate-700 shrink-0 mt-0.5 sm:mt-0">
          <Info className="w-4 h-4" />
        </div>
        <div className="flex-1 text-xs text-slate-700 leading-normal">
          <span className="font-semibold text-slate-900 mr-1.5">
            Decision-support prototype:
          </span>
          This dashboard highlights meaningful changes and domain-level attention signals from available observations. It does not diagnose PCOS or provide a risk probability.
        </div>
        <div className="hidden md:flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-200/80 border border-slate-300/80 text-[11px] font-mono text-slate-700 shrink-0">
          <span>Non-Diagnostic</span>
        </div>
      </div>
    </div>
  );
};
