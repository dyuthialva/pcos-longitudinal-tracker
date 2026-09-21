import React, { useState } from 'react';
import type { Patient } from '../../types/clinical';
import { TrendChart } from '../trends/TrendChart';
import { AVAILABLE_TREND_PARAMETERS } from '../../data/mockPatients';
import { Calendar } from 'lucide-react';

interface TrendsPageProps {
  patient: Patient;
}

export const TrendsPage: React.FC<TrendsPageProps> = ({ patient }) => {
  const [activeTabParam, setActiveTabParam] = useState<string>('Weight');


  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-slate-900 m-0">
                Longitudinal Trajectory Explorer
              </h2>
              <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                Patient {patient.id}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Inspect multi-encounter biomarker curves with standard clinical reference bounds.
            </p>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono bg-slate-50 px-2.5 py-1.5 rounded border border-slate-200">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span>{patient.firstVisitDate} — {patient.latestVisitDate}</span>
          </div>
        </div>

        {/* Quick Parameter Filter Pills */}
        <div className="mt-4 space-y-2">
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
            Select Tracked Biomarker / Observation
          </span>
          <div className="flex flex-wrap gap-2">
            {AVAILABLE_TREND_PARAMETERS.map((param) => {
              const isSelected = activeTabParam === param.key;
              return (
                <button
                  key={param.key}
                  onClick={() => setActiveTabParam(param.key)}
                  className={`px-3 py-1.5 rounded text-xs font-medium transition flex items-center gap-1.5 ${
                    isSelected
                      ? 'bg-teal-700 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  <span>{param.label}</span>
                  <span className={`text-[10px] font-mono ${isSelected ? 'text-teal-200' : 'text-slate-400'}`}>
                    ({param.unit})
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Trend Interactive Chart */}
      <TrendChart patient={patient} initialParameter={activeTabParam} />

      {/* Domain Multi-Grid Snapshot */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
        <h3 className="text-sm font-semibold text-slate-900 mb-3">
          Tracked Biomarker Reference Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {AVAILABLE_TREND_PARAMETERS.map((param) => (
            <div
              key={param.key}
              onClick={() => setActiveTabParam(param.key)}
              className={`p-3 rounded-lg border cursor-pointer transition ${
                activeTabParam === param.key
                  ? 'border-teal-500 bg-teal-50/30 ring-1 ring-teal-500/20'
                  : 'border-slate-200 bg-slate-50/50 hover:bg-slate-100/60'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-xs text-slate-900">
                  {param.label}
                </span>
                <span className="text-[10px] font-mono text-slate-500 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                  {param.unit}
                </span>
              </div>
              <div className="text-[11px] text-slate-500 mt-2 flex items-center justify-between">
                <span>Domain: {param.domain}</span>
              </div>
              <div className="text-[10px] font-mono text-slate-400 mt-1">
                Ref: {param.refMin} – {param.refMax} {param.unit}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
