import React from 'react';
import type { ClinicalDelta } from '../../types/clinical';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { StatusTag } from '../common/Badge';


interface ChangeCardProps {
  delta: ClinicalDelta;
  onDrillDownDomain?: (domain: string) => void;
}

export const ChangeCard: React.FC<ChangeCardProps> = ({ delta, onDrillDownDomain }) => {
  const getDirectionIcon = () => {
    if (delta.direction === 'up') {
      return <ArrowUpRight className="w-4 h-4 text-rose-600" />;
    }
    if (delta.direction === 'down') {
      return <ArrowDownRight className="w-4 h-4 text-emerald-600" />;
    }
    return <Minus className="w-4 h-4 text-slate-400" />;
  };

  const getDomainColor = (domain: string) => {
    switch (domain) {
      case 'Reproductive':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'Hyperandrogenism':
        return 'bg-pink-50 text-pink-700 border-pink-200';
      case 'Metabolic':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'Lifestyle':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Psychological':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'Sleep':
        return 'bg-cyan-50 text-cyan-700 border-cyan-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 hover:border-slate-300 transition-colors shadow-2xs">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded border ${getDomainColor(delta.domain)}`}>
            {delta.domain}
          </span>
          <h4 className="text-sm font-semibold text-slate-900">
            {delta.parameter}
          </h4>
        </div>
        <StatusTag status={delta.statusTag} severity={delta.statusSeverity} />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 py-2.5 px-3 bg-slate-50 rounded-md border border-slate-100 my-2">
        {/* Previous Value */}
        <div>
          <span className="text-[10px] uppercase font-semibold text-slate-400 block">
            Previous
          </span>
          <span className="text-xs font-mono font-medium text-slate-600">
            {delta.previousValue !== null ? `${delta.previousValue} ${delta.unit}` : 'Baseline / None'}
          </span>
        </div>

        {/* Current Value */}
        <div>
          <span className="text-[10px] uppercase font-semibold text-slate-400 block">
            Current
          </span>
          <span className="text-xs font-mono font-bold text-slate-900">
            {delta.currentValue} {delta.unit}
          </span>
        </div>

        {/* Delta */}
        <div>
          <span className="text-[10px] uppercase font-semibold text-slate-400 block">
            Delta
          </span>
          <div className="flex items-center gap-1">
            {getDirectionIcon()}
            <span className="text-xs font-mono font-bold text-slate-900">
              {delta.deltaDisplay}
            </span>
          </div>
        </div>
      </div>

      {delta.clinicalNote && (
        <p className="text-xs text-slate-600 mt-2 flex items-start gap-1.5 leading-relaxed">
          <span className="text-slate-400 font-semibold">•</span>
          <span>{delta.clinicalNote}</span>
        </p>
      )}

      {onDrillDownDomain && (
        <div className="mt-3 pt-2 border-t border-slate-100 flex justify-end">
          <button
            onClick={() => onDrillDownDomain(delta.domain)}
            className="text-[11px] font-medium text-teal-700 hover:text-teal-900 transition"
          >
            Inspect {delta.domain} domain →
          </button>
        </div>
      )}
    </div>
  );
};
