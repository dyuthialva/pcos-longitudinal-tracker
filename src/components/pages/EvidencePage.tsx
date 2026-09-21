import React, { useState } from 'react';
import type { Patient, Visit } from '../../types/clinical';
import { EvidenceTable } from '../evidence/EvidenceTable';


interface EvidencePageProps {
  patient: Patient;
  selectedVisit: Visit;
  onSelectVisit: (visitId: string) => void;
}

export const EvidencePage: React.FC<EvidencePageProps> = ({
  patient,
  selectedVisit,
  onSelectVisit,
}) => {
  const [viewScope, setViewScope] = useState<'current' | 'all'>('current');

  // Aggregated observations across all visits if "all" is selected
  const allObservations = patient.visits.flatMap((v) => v.observations);

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-slate-900 m-0">
                Evidence Audit & Traceability Log
              </h2>
              <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                Patient {patient.id}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Inspect raw clinical data sources, lab reports, self-reports, and clinician annotations.
            </p>
          </div>

          {/* Scope Selector */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 self-start sm:self-auto">
            <button
              onClick={() => setViewScope('current')}
              className={`px-3 py-1 text-xs font-medium rounded transition ${
                viewScope === 'current'
                  ? 'bg-white text-slate-900 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Current Visit ({selectedVisit.date})
            </button>
            <button
              onClick={() => setViewScope('all')}
              className={`px-3 py-1 text-xs font-medium rounded transition ${
                viewScope === 'all'
                  ? 'bg-white text-slate-900 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All Visits ({allObservations.length})
            </button>
          </div>
        </div>

        {/* Current Visit Quick Selector */}
        {viewScope === 'current' && (
          <div className="mt-4 flex items-center gap-3 text-xs">
            <span className="text-slate-500">Active Encounter:</span>
            <select
              value={selectedVisit.id}
              onChange={(e) => onSelectVisit(e.target.value)}
              className="bg-slate-50 border border-slate-300 font-mono text-xs rounded px-2.5 py-1 text-slate-900 font-medium cursor-pointer"
            >
              {patient.visits.map((v) => (
                <option key={v.id} value={v.id}>
                  Visit {v.visitNumber} ({v.date}) • {v.observations.length} observations
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Main Evidence Table */}
      <EvidenceTable
        observations={viewScope === 'current' ? selectedVisit.observations : allObservations}
        visit={viewScope === 'current' ? selectedVisit : undefined}
      />
    </div>
  );
};
