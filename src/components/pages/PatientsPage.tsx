import { type FC, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ChevronRight, Layers } from 'lucide-react';
import { DataCompleteness } from '../common/DataCompleteness';
import { AttentionBadge } from '../common/Badge';
import { EmptyState } from '../common/EmptyState';
import { useClinicalData } from '../../clinical/ClinicalDataContext';
import { meaningfulChangeCount, sortWorklist, topAttention } from '../../lib/attention';

export const PatientsPage: FC = () => {
  const { patients } = useClinicalData();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');

  const filteredPatients = sortWorklist(
    patients.filter(
      (p) =>
        p.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.syntheticCohortLabel.toLowerCase().includes(searchTerm.toLowerCase()),
    ),
  );

  return (
    <div className="space-y-6 pb-12">
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 m-0">Clinician worklist</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Ranked by current attention band, then recency and data completeness. Identifiers only —
              no patient names.
            </p>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
            {patients.length} records
          </span>
        </div>

        <div className="mt-4 relative max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="search"
            placeholder="Search by patient ID (e.g. P-0042)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-teal-600"
          />
        </div>
      </div>

      {filteredPatients.length === 0 ? (
        <EmptyState
          title="No matching records"
          description="Adjust the search, or confirm this clinician session is authorized for the expected cohort."
        />
      ) : (
        <div className="bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Patient ID</th>
                  <th className="py-3 px-4">Age</th>
                  <th className="py-3 px-4">Last visit</th>
                  <th className="py-3 px-4">Top domain</th>
                  <th className="py-3 px-4">Band</th>
                  <th className="py-3 px-4">Completeness</th>
                  <th className="py-3 px-4">Meaningful changes</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredPatients.map((p) => {
                  const attention = topAttention(p);
                  return (
                    <tr
                      key={p.id}
                      onClick={() => navigate(`/patients/${p.id}`)}
                      className="hover:bg-slate-50/80 transition-colors cursor-pointer"
                    >
                      <td className="py-3 px-4">
                        <span className="font-mono font-bold text-slate-900 text-sm">{p.id}</span>
                      </td>
                      <td className="py-3 px-4 text-slate-700">{p.age}</td>
                      <td className="py-3 px-4 font-mono text-slate-700 whitespace-nowrap">
                        {p.latestVisitDate}
                      </td>
                      <td className="py-3 px-4 text-slate-700">{attention.domain ?? '—'}</td>
                      <td className="py-3 px-4">
                        <AttentionBadge band={attention.band} size="sm" />
                      </td>
                      <td className="py-3 px-4">
                        <div className="max-w-[140px]">
                          <DataCompleteness percentage={p.dataCompleteness} size="sm" />
                        </div>
                      </td>
                      <td className="py-3 px-4 font-mono">
                        <span className="inline-flex items-center gap-1">
                          <Layers className="w-3.5 h-3.5 text-slate-400" />
                          {meaningfulChangeCount(p)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/patients/${p.id}`);
                          }}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3 py-1.5 rounded transition"
                        >
                          Open chart
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
      )}
    </div>
  );
};
