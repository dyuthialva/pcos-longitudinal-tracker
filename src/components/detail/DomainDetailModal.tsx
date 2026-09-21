import React, { useState } from 'react';
import type {
  DomainType,
  Patient,
  Visit,
} from '../../types/clinical';
import { AttentionBadge, FlagBadge } from '../common/Badge';
import {
  X,
  TrendingUp,
  FileSpreadsheet,
  Activity,
} from 'lucide-react';

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { extractParameterTrend } from '../../data/mockPatients';

interface DomainDetailModalProps {
  domain: DomainType | null;
  patient: Patient;
  visit: Visit;
  onClose: () => void;
}

export const DomainDetailModal: React.FC<DomainDetailModalProps> = ({
  domain,
  patient,
  visit,
  onClose,
}) => {
  if (!domain) return null;

  const domainScore = visit.domainScores[domain];
  const domainDeltas = visit.deltas.filter((d) => d.domain === domain);
  const domainObservations = visit.observations.filter((o) => o.domain === domain);

  // Available parameters for trend line in this domain
  const availableParameters = Array.from(
    new Set(domainObservations.map((o) => o.parameter))
  );

  const [selectedParam, setSelectedParam] = useState<string>(
    availableParameters[0] || ''
  );

  const trendPoints = selectedParam
    ? extractParameterTrend(patient, selectedParam)
    : [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full border border-slate-200 overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-lg bg-teal-800 text-teal-200">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-white m-0">
                  {domain} Domain
                </h3>
                {domainScore && <AttentionBadge band={domainScore.band} size="sm" />}
              </div>
              <p className="text-xs text-slate-400 m-0 mt-0.5">
                Detailed change analysis & contributing evidence • Patient {patient.id}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Modal Body */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {/* Attention Score Summary Banner */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                Domain Attention Score
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                {domainScore?.isInsufficientData ? (
                  <span className="text-sm font-semibold text-slate-500 italic">
                    Insufficient Data
                  </span>
                ) : (
                  <>
                    <span className="text-2xl font-bold font-mono text-slate-900">
                      {domainScore?.score ?? '—'}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">/ 100</span>
                  </>
                )}
              </div>
            </div>

            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                Attention Band
              </span>
              <div className="mt-1">
                {domainScore && <AttentionBadge band={domainScore.band} size="md" />}
              </div>
            </div>

            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                Contributing Observations
              </span>
              <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
                {domainObservations.length}
                <span className="text-xs font-sans text-slate-500 font-normal ml-2">
                  logged for this visit
                </span>
              </div>
            </div>
          </div>

          {/* What Changed? */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
              <TrendingUp className="w-4 h-4 text-teal-700" />
              <h4 className="text-sm font-semibold text-slate-900 m-0">
                What Changed Since Previous Visit?
              </h4>
            </div>

            {domainDeltas.length === 0 ? (
              <div className="p-4 rounded-lg bg-slate-50 text-xs text-slate-500 font-mono">
                No parameter changes recorded for the {domain} domain between this and the preceding encounter.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {domainDeltas.map((delta) => (
                  <div
                    key={delta.id}
                    className="p-3.5 rounded-lg border border-slate-200 bg-white shadow-2xs space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-slate-900">
                        {delta.parameter}
                      </span>
                      <span className="text-[11px] font-mono font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded">
                        {delta.deltaDisplay}
                      </span>
                    </div>

                    <div className="text-xs text-slate-600 flex items-center gap-2 font-mono">
                      <span>{delta.previousValue !== null ? `${delta.previousValue} ${delta.unit}` : 'Baseline'}</span>
                      <span>→</span>
                      <span className="font-bold text-slate-900">{delta.currentValue} {delta.unit}</span>
                    </div>

                    {delta.clinicalNote && (
                      <p className="text-[11px] text-slate-500 mt-1 leading-normal border-t border-slate-100 pt-1.5">
                        {delta.clinicalNote}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Trend Visualization if data available */}
          {availableParameters.length > 0 && (
            <div className="space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
                <h4 className="text-sm font-semibold text-slate-900 m-0">
                  Longitudinal Trend Curve
                </h4>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">Metric:</span>
                  <select
                    value={selectedParam}
                    onChange={(e) => setSelectedParam(e.target.value)}
                    className="text-xs bg-slate-50 border border-slate-300 rounded px-2.5 py-1 font-medium cursor-pointer"
                  >
                    {availableParameters.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="h-56 w-full bg-slate-50/50 p-2 rounded-lg border border-slate-200">
                {trendPoints.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-slate-400 font-mono">
                    Insufficient longitudinal points for {selectedParam}.
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendPoints} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="visitDate" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} domain={['auto', 'auto']} />
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const pt = payload[0].payload;
                            return (
                              <div className="bg-slate-900 text-white p-2 rounded shadow text-xs font-mono">
                                <div>{pt.visitDate}</div>
                                <div className="text-teal-300 font-bold">{pt.value} {pt.unit}</div>
                                <div className="text-slate-400 text-[10px]">{pt.source}</div>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#0f766e"
                        strokeWidth={2.5}
                        dot={{ r: 4, fill: '#0f766e', stroke: '#ffffff', strokeWidth: 2 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          )}

          {/* Traceable Evidence Table */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
              <FileSpreadsheet className="w-4 h-4 text-teal-700" />
              <h4 className="text-sm font-semibold text-slate-900 m-0">
                Traceable Raw Observations ({domainObservations.length})
              </h4>
            </div>

            {domainObservations.length === 0 ? (
              <div className="p-4 bg-slate-50 text-xs text-slate-500 font-mono text-center rounded border border-dashed border-slate-300">
                No raw observations recorded for {domain} in this visit.
              </div>
            ) : (
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider text-[10px] border-b border-slate-200">
                    <tr>
                      <th className="py-2 px-3">Parameter</th>
                      <th className="py-2 px-3">Value</th>
                      <th className="py-2 px-3">Ref. Range</th>
                      <th className="py-2 px-3">Flag</th>
                      <th className="py-2 px-3">Recorded Date</th>
                      <th className="py-2 px-3">Source</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {domainObservations.map((obs) => (
                      <tr key={obs.id} className="hover:bg-slate-50/70">
                        <td className="py-2 px-3 font-medium text-slate-900">
                          {obs.parameter}
                        </td>
                        <td className="py-2 px-3 font-mono font-bold text-slate-900">
                          {obs.value} {obs.unit}
                        </td>
                        <td className="py-2 px-3 font-mono text-slate-500">
                          {obs.referenceRange || '—'}
                        </td>
                        <td className="py-2 px-3">
                          <FlagBadge flag={obs.flag} />
                        </td>
                        <td className="py-2 px-3 font-mono text-slate-600">
                          {obs.date}
                        </td>
                        <td className="py-2 px-3 text-slate-600 font-medium">
                          {obs.source}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between shrink-0">
          <span className="text-xs text-slate-500">
            Decision support only • Non-diagnostic domain signal
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-white bg-slate-900 rounded hover:bg-slate-800 transition"
          >
            Close Drill-Down
          </button>
        </div>
      </div>
    </div>
  );
};
