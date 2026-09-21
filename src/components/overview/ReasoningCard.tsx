import React from 'react';
import type { Visit } from '../../types/clinical';
import { FileText, Shield } from 'lucide-react';


interface ReasoningCardProps {
  visit: Visit;
}

export const ReasoningCard: React.FC<ReasoningCardProps> = ({ visit }) => {
  return (
    <section className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs mb-6">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-teal-50 text-teal-700">
            <FileText className="w-4 h-4" />
          </div>
          <h2 className="text-base font-semibold text-slate-900 m-0">
            Clinical Context
          </h2>
        </div>
        <span className="text-[11px] font-mono text-slate-400 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
          Rule-Constrained Reasoning
        </span>
      </div>

      <div className="mt-4 p-4 rounded-lg bg-slate-50/70 border border-slate-200/80">
        <p className="text-sm text-slate-800 leading-relaxed font-normal">
          {visit.reasoningNarrative}
        </p>

        <div className="mt-3 pt-3 border-t border-slate-200/60 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-500 gap-2">
          <div className="flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-teal-600" />
            <span className="text-[11px]">
              Summary synthesizes computed deltas into structured narrative without diagnostic inference.
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            Enc. #{visit.visitNumber} ({visit.date})
          </span>
        </div>
      </div>
    </section>
  );
};
