import React, { useState } from 'react';
import type { Patient } from '../../types/clinical';
import { DataCompleteness } from '../common/DataCompleteness';
import { Search, ChevronRight, Layers } from 'lucide-react';


interface PatientsPageProps {
  patients: Patient[];
  activePatientId: string;
  onSelectPatient: (patientId: string) => void;
}

export const PatientsPage: React.FC<PatientsPageProps> = ({
  patients,
  activePatientId,
  onSelectPatient,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredPatients = patients.filter(
    (p) =>
      p.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.syntheticCohortLabel.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 m-0">
              Synthetic Patient Cohort
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Select a synthetic patient record to inspect longitudinal visits, domain attention scores, and raw observations.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
              {patients.length} Synthetic Profiles
            </span>
          </div>
        </div>

        {/* Search Bar */}
        <div className="mt-4 relative max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Patient ID (e.g. P-0042)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-teal-600 font-sans"
          />
        </div>
      </div>

      {/* Patient Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Patient ID</th>
                <th className="py-3 px-4">Synthetic Cohort</th>
                <th className="py-3 px-4">Visits Tracked</th>
                <th className="py-3 px-4">Latest Visit</th>
                <th className="py-3 px-4">Overall Completeness</th>
                <th className="py-3 px-4">Last Updated</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredPatients.map((p) => {
                const isActive = p.id === activePatientId;
                return (
                  <tr
                    key={p.id}
                    onClick={() => onSelectPatient(p.id)}
                    className={`hover:bg-slate-50/80 transition-colors cursor-pointer ${
                      isActive ? 'bg-teal-50/40' : ''
                    }`}
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-slate-900 text-sm">
                          {p.id}
                        </span>
                        {isActive && (
                          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-teal-100 text-teal-800 border border-teal-200">
                            Active
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-3 px-4 text-slate-600">
                      {p.syntheticCohortLabel}
                    </td>

                    <td className="py-3 px-4 font-mono font-medium text-slate-800">
                      <span className="inline-flex items-center gap-1">
                        <Layers className="w-3.5 h-3.5 text-slate-400" />
                        {p.totalVisits} encounters
                      </span>
                    </td>

                    <td className="py-3 px-4 font-mono text-slate-700 whitespace-nowrap">
                      {p.latestVisitDate}
                    </td>

                    <td className="py-3 px-4">
                      <div className="max-w-[140px]">
                        <DataCompleteness percentage={p.dataCompleteness} size="sm" />
                      </div>
                    </td>

                    <td className="py-3 px-4 font-mono text-slate-500 whitespace-nowrap">
                      {p.lastUpdated}
                    </td>

                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectPatient(p.id);
                        }}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3 py-1.5 rounded transition"
                      >
                        <span>Open Dashboard</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
