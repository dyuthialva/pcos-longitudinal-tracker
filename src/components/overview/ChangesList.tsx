import React from 'react';
import type { Visit } from '../../types/clinical';

import { ChangeCard } from './ChangeCard';
import { EmptyState } from '../common/EmptyState';
import { History, ArrowRight, CheckCircle2 } from 'lucide-react';

interface ChangesListProps {
  visit: Visit;
  onViewAllObservations: () => void;
  onDrillDownDomain: (domain: string) => void;
}

export const ChangesList: React.FC<ChangesListProps> = ({
  visit,
  onViewAllObservations,
  onDrillDownDomain,
}) => {
  const meaningfulDeltas = visit.deltas.filter((d) => d.isMeaningful);
  const isBaselineVisit = visit.visitNumber === 1 || visit.deltas.length === 0;

  return (
    <section className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-slate-900 m-0">
              Changes Since Previous Visit
            </h2>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
              {meaningfulDeltas.length} detected
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Meaningful changes detected between the selected visit and the previous visit.
          </p>
        </div>

        <button
          onClick={onViewAllObservations}
          className="inline-flex items-center gap-1 text-xs font-medium text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100/80 px-3 py-1.5 rounded transition shrink-0 self-start sm:self-auto"
        >
          <span>View all observations</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="mt-4">
        {isBaselineVisit ? (
          <EmptyState
            icon={History}
            title="No previous visit available"
            description="This visit cannot be compared longitudinally because no earlier visit is available in the record (baseline intake)."
          />
        ) : meaningfulDeltas.length === 0 ? (
          <EmptyState
            icon={CheckCircle2}
            title="No meaningful changes detected"
            description="All recorded parameters remained stable within established clinical variation thresholds relative to the previous visit."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {meaningfulDeltas.map((delta) => (
              <ChangeCard
                key={delta.id}
                delta={delta}
                onDrillDownDomain={onDrillDownDomain}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
};
