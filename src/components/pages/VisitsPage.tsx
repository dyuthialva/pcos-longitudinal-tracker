import React from 'react';
import type { Patient } from '../../types/clinical';
import { DataCompleteness } from '../common/DataCompleteness';
import { Calendar, FileText, ChevronRight } from 'lucide-react';


interface VisitsPageProps {
  patient: Patient;
  selectedVisitId: string;
  onSelectVisit: (visitId: string) => void;
  onNavigateToOverview: () => void;
}

export const VisitsPage: React.FC<VisitsPageProps> = ({
  patient,
  selectedVisitId,
  onSelectVisit,
  onNavigateToOverview,
}) => {
  // Sort visits newest first
  const sortedVisits = [...patient.visits].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-slate-900 m-0">
                Longitudinal Visit History
              </h2>
              <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                Patient {patient.id}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Chronological records of all clinical encounters, laboratory panels, and patient questionnaires.
            </p>
          </div>

          <div className="text-xs font-mono text-slate-600 bg-slate-50 px-3 py-1.5 rounded border border-slate-200">
            {patient.totalVisits} Encounters Recorded
          </div>
        </div>
      </div>

      {/* Visits Chronological List / Cards */}
      <div className="space-y-4">
        {sortedVisits.map((visit) => {
          const isSelected = visit.id === selectedVisitId;
          const meaningfulDeltas = visit.deltas.filter((d) => d.isMeaningful);
          const changedDomains = Array.from(new Set(meaningfulDeltas.map((d) => d.domain)));

          return (
            <div
              key={visit.id}
              className={`bg-white border rounded-lg p-5 transition-all shadow-xs ${
                isSelected
                  ? 'border-teal-500 ring-1 ring-teal-500/20'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${isSelected ? 'bg-teal-700 text-white' : 'bg-slate-100 text-slate-700'}`}>
                    <Calendar className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-slate-900 font-mono m-0">
                        {visit.date}
                      </h3>
                      <span className="text-xs font-mono text-slate-500">
                        (Visit {visit.visitNumber})
                      </span>
                      {isSelected && (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-200">
                          Currently Selected
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-slate-500 mt-0.5 block">
                      Source: {visit.sourceType}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">
                      Data Completeness
                    </span>
                    <div className="w-32 mt-1">
                      <DataCompleteness percentage={visit.dataCompleteness} size="sm" />
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      onSelectVisit(visit.id);
                      onNavigateToOverview();
                    }}
                    className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded transition ${
                      isSelected
                        ? 'bg-teal-700 text-white hover:bg-teal-800'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    <span>View In Overview</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Grid Metadata */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
                <div className="p-3 bg-slate-50 rounded border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">
                    Observations Logged
                  </span>
                  <span className="text-sm font-bold font-mono text-slate-900 mt-0.5 block">
                    {visit.totalObservations} raw entries
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">
                    Meaningful Changes
                  </span>
                  <span className="text-sm font-bold font-mono text-slate-900 mt-0.5 block">
                    {visit.visitNumber === 1
                      ? 'Baseline (0 deltas)'
                      : `${meaningfulDeltas.length} parameters changed`}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">
                    Changed Domains
                  </span>
                  <span className="text-xs font-medium text-slate-800 mt-1 block truncate">
                    {changedDomains.length > 0
                      ? changedDomains.join(', ')
                      : 'None / Stable'}
                  </span>
                </div>
              </div>

              {/* Narrative Snapshot */}
              <div className="mt-3 p-3 bg-slate-50/60 rounded border border-slate-200/60 text-xs text-slate-600 leading-relaxed flex items-start gap-2">
                <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                <span>{visit.reasoningNarrative}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
