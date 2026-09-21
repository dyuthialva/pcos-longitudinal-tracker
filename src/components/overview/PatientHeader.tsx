import React from 'react';
import type { Patient, Visit } from '../../types/clinical';
import { Calendar, Layers, User } from 'lucide-react';

import { DataCompleteness } from '../common/DataCompleteness';

interface PatientHeaderProps {
  patient: Patient;
  selectedVisit: Visit;
  onSelectVisit: (visitId: string) => void;
}

export const PatientHeader: React.FC<PatientHeaderProps> = ({
  patient,
  selectedVisit,
  onSelectVisit,
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Patient Identity & Meta */}
        <div className="space-y-1">
          <div className="flex items-center gap-2.5 flex-wrap">
            <div className="flex items-center gap-1.5 bg-slate-100 text-slate-800 px-2.5 py-1 rounded border border-slate-200 font-mono text-xs font-semibold">
              <User className="w-3.5 h-3.5 text-slate-500" />
              <span>Patient {patient.id}</span>
            </div>
            <span className="text-xs px-2 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-200 font-medium">
              Synthetic Record
            </span>
            <span className="text-xs text-slate-400 font-normal">
              Age: {patient.age} yrs
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-600 pt-1 flex-wrap">
            <div className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <span>
                <strong className="text-slate-800 font-semibold">{patient.totalVisits}</strong> visits tracked
              </span>
            </div>
            <span className="text-slate-300">•</span>
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>
                Latest visit: <strong className="text-slate-800 font-semibold">{patient.latestVisitDate}</strong>
              </span>
            </div>
            <span className="text-slate-300">•</span>
            <div className="flex items-center gap-2">
              <span className="text-slate-500">Data completeness:</span>
              <DataCompleteness percentage={selectedVisit.dataCompleteness} size="sm" />
            </div>
          </div>
        </div>

        {/* Visit Selector Dropdown */}
        <div className="flex items-center gap-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200 shrink-0">
          <div className="flex flex-col">
            <label
              htmlFor="visit-selector"
              className="text-[10px] uppercase font-bold tracking-wider text-slate-500"
            >
              Selected Visit
            </label>
            <div className="flex items-center gap-2 mt-0.5">
              <select
                id="visit-selector"
                value={selectedVisit.id}
                onChange={(e) => onSelectVisit(e.target.value)}
                className="bg-white text-xs font-medium text-slate-900 border border-slate-300 rounded px-2.5 py-1.5 shadow-2xs focus:outline-none focus:ring-1 focus:ring-teal-600 font-mono cursor-pointer"
              >
                {patient.visits.map((v) => (
                  <option key={v.id} value={v.id}>
                    Visit {v.visitNumber} ({v.date})
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="hidden sm:block border-l border-slate-200 pl-3">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 block">
              Source Log
            </span>
            <span className="text-xs text-slate-600 block max-w-[130px] truncate" title={selectedVisit.sourceType}>
              {selectedVisit.sourceType}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
