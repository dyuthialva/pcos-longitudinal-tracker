import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import type { Patient } from '../../types/clinical';
import { AVAILABLE_TREND_PARAMETERS, extractParameterTrend } from '../../data/mockPatients';
import { FlagBadge } from '../common/Badge';

interface TrendChartProps {
  patient: Patient;
  initialParameter?: string;
}

export const TrendChart: React.FC<TrendChartProps> = ({
  patient,
  initialParameter = 'Weight',
}) => {
  const [selectedParamKey, setSelectedParamKey] = useState<string>(initialParameter);

  const activeParamConfig =
    AVAILABLE_TREND_PARAMETERS.find((p) => p.key === selectedParamKey) ||
    AVAILABLE_TREND_PARAMETERS[0];

  const trendData = extractParameterTrend(patient, activeParamConfig.key);

  // Custom Clinical Tooltip
  const CustomTooltip = ({ active, payload }: any) => {

    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload;
      return (
        <div className="bg-slate-900 text-white p-3 rounded-lg shadow-lg border border-slate-800 text-xs font-sans space-y-1">
          <div className="text-[10px] uppercase tracking-wider text-slate-400 font-mono">
            {dataPoint.visitDate} (Enc. #{dataPoint.visitNumber})
          </div>
          <div className="text-sm font-bold text-teal-300 font-mono">
            {dataPoint.value} {dataPoint.unit}
          </div>
          <div className="text-slate-300 pt-1 border-t border-slate-800 flex items-center justify-between gap-4">
            <span className="text-slate-400">Source:</span>
            <span className="font-medium text-white">{dataPoint.source}</span>
          </div>
          {dataPoint.flag && dataPoint.flag !== 'normal' && (
            <div className="pt-1">
              <FlagBadge flag={dataPoint.flag} />
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
      {/* Controls Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900 m-0">
              Longitudinal Trends
            </h3>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">
              {patient.totalVisits} Enrolled Visits
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Chronological biomarker and observation trajectory across recorded encounters.
          </p>
        </div>

        {/* Parameter Selector Pills / Dropdown */}
        <div className="flex items-center gap-2 flex-wrap">
          <label htmlFor="trend-param-select" className="sr-only">
            Select Parameter
          </label>
          <select
            id="trend-param-select"
            value={selectedParamKey}
            onChange={(e) => setSelectedParamKey(e.target.value)}
            className="bg-slate-50 border border-slate-300 text-xs font-semibold text-slate-800 rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-teal-600 cursor-pointer"
          >
            {AVAILABLE_TREND_PARAMETERS.map((param) => (
              <option key={param.key} value={param.key}>
                {param.label} ({param.unit}) • {param.domain}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Parameter Info & Reference Ranges */}
      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs bg-slate-50 px-3 py-2 rounded border border-slate-100">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-800">{activeParamConfig.label}</span>
          <span className="text-slate-400">•</span>
          <span className="text-slate-600 font-mono">Domain: {activeParamConfig.domain}</span>
        </div>
        {activeParamConfig.refMin !== undefined && activeParamConfig.refMax !== undefined && (
          <div className="text-slate-500 font-mono text-[11px]">
            Reference Guidance: {activeParamConfig.refMin} – {activeParamConfig.refMax} {activeParamConfig.unit}
          </div>
        )}
      </div>

      {/* Chart Canvas */}
      <div className="h-72 w-full mt-4">
        {trendData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-slate-400 font-mono">
            No longitudinal data points logged for {activeParamConfig.label}.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={trendData}
              margin={{ top: 15, right: 25, left: -10, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="visitDate"
                stroke="#64748b"
                tick={{ fontSize: 11, fontFamily: 'monospace' }}
                tickLine={false}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fontSize: 11, fontFamily: 'monospace' }}
                tickLine={false}
                domain={['auto', 'auto']}
                unit={` ${activeParamConfig.unit}`}
              />
              <Tooltip content={<CustomTooltip />} />
              {activeParamConfig.refMin !== undefined && (
                <ReferenceLine
                  y={activeParamConfig.refMin}
                  stroke="#94a3b8"
                  strokeDasharray="4 4"
                  strokeOpacity={0.6}
                />
              )}
              {activeParamConfig.refMax !== undefined && (
                <ReferenceLine
                  y={activeParamConfig.refMax}
                  stroke="#94a3b8"
                  strokeDasharray="4 4"
                  strokeOpacity={0.6}
                />
              )}
              <Line
                type="monotone"
                dataKey="value"
                stroke="#0f766e"
                strokeWidth={2.5}
                dot={{ r: 5, fill: '#0f766e', strokeWidth: 2, stroke: '#ffffff' }}
                activeDot={{ r: 7, fill: '#14b8a6', strokeWidth: 2, stroke: '#0f766e' }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
        <span>* Hover individual points for encounter date, numerical value, and source record.</span>
        <span>Standard clinical axis auto-scaling</span>
      </div>
    </div>
  );
};
