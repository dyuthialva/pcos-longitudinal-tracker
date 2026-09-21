import React, { useState, useMemo } from 'react';
import type { DomainType, Observation, ObservationSource, Visit } from '../../types/clinical';
import { FlagBadge } from '../common/Badge';
import { Search } from 'lucide-react';


interface EvidenceTableProps {
  observations: Observation[];
  visit?: Visit;
  initialDomainFilter?: DomainType | 'ALL';
  showAllVisitsToggle?: boolean;
}

export const EvidenceTable: React.FC<EvidenceTableProps> = ({
  observations,
  visit,
  initialDomainFilter = 'ALL',
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [domainFilter, setDomainFilter] = useState<string>(initialDomainFilter);
  const [sourceFilter, setSourceFilter] = useState<string>('ALL');

  const filteredObservations = useMemo(() => {
    return observations.filter((obs) => {
      const matchesSearch =
        obs.parameter.toLowerCase().includes(searchTerm.toLowerCase()) ||
        String(obs.value).toLowerCase().includes(searchTerm.toLowerCase());

      const matchesDomain =
        domainFilter === 'ALL' || obs.domain === domainFilter;

      const matchesSource =
        sourceFilter === 'ALL' || obs.source === sourceFilter;

      return matchesSearch && matchesDomain && matchesSource;
    });
  }, [observations, searchTerm, domainFilter, sourceFilter]);

  const allDomains: DomainType[] = [
    'Reproductive',
    'Hyperandrogenism',
    'Metabolic',
    'Lifestyle',
    'Psychological',
    'Sleep',
  ];

  const allSources: ObservationSource[] = [
    'Lab report',
    'Self report',
    'Clinician entry',
    'Computed',
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900 m-0">
              Evidence Drill-Down
            </h3>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700">
              {filteredObservations.length} observations
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Raw observations contributing to computed domain attention signals.
          </p>
        </div>

        {visit && (
          <div className="text-xs text-slate-500 font-mono self-start sm:self-auto bg-slate-50 px-2.5 py-1 rounded border border-slate-200">
            Selected: Enc. #{visit.visitNumber} ({visit.date})
          </div>
        )}
      </div>

      {/* Filter Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 my-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search parameter or value..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-teal-600 font-sans"
          />
        </div>

        {/* Domain Filter */}
        <div>
          <select
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
            className="w-full py-1.5 px-2.5 text-xs bg-slate-50 border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-teal-600 font-sans cursor-pointer"
          >
            <option value="ALL">All Domains (6)</option>
            {allDomains.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        {/* Source Filter */}
        <div>
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="w-full py-1.5 px-2.5 text-xs bg-slate-50 border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-teal-600 font-sans cursor-pointer"
          >
            <option value="ALL">All Sources (4)</option>
            {allSources.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Observations Table */}
      <div className="overflow-x-auto border border-slate-200 rounded-lg">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
            <tr>
              <th className="py-2.5 px-3">Parameter</th>
              <th className="py-2.5 px-3">Value</th>
              <th className="py-2.5 px-3">Ref. Range</th>
              <th className="py-2.5 px-3">Flag</th>
              <th className="py-2.5 px-3">Domain</th>
              <th className="py-2.5 px-3">Date</th>
              <th className="py-2.5 px-3">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-sans">
            {filteredObservations.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-400 font-mono">
                  No observation records match the selected filters.
                </td>
              </tr>
            ) : (
              filteredObservations.map((obs) => (
                <tr
                  key={obs.id}
                  className="hover:bg-slate-50/80 transition-colors"
                >
                  <td className="py-2.5 px-3 font-medium text-slate-900">
                    {obs.parameter}
                  </td>
                  <td className="py-2.5 px-3 font-mono font-bold text-slate-900">
                    {obs.value} {obs.unit}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-500">
                    {obs.referenceRange || '—'}
                  </td>
                  <td className="py-2.5 px-3">
                    <FlagBadge flag={obs.flag} />
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="text-[11px] text-slate-700 bg-slate-100 px-2 py-0.5 rounded font-mono">
                      {obs.domain}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-600 whitespace-nowrap">
                    {obs.date}
                  </td>
                  <td className="py-2.5 px-3 text-slate-600">
                    <span className="inline-flex items-center gap-1 font-medium">
                      {obs.source}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
        <span>* Every domain score in this prototype maps strictly to the raw observations above.</span>
        <span>Traceable Audit Trail</span>
      </div>
    </div>
  );
};
