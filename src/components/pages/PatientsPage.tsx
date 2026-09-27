import { type FC, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ChevronRight, UserPlus, X, AlertCircle, ShieldAlert } from 'lucide-react';
import { DataCompleteness } from '../common/DataCompleteness';
import { AttentionBadge } from '../common/Badge';
import { EmptyState } from '../common/EmptyState';
import { useClinicalData } from '../../clinical/ClinicalDataContext';
import { meaningfulChangeCount, sortWorklist, topAttention } from '../../lib/attention';
import { ClinicalApiService } from '../../services/clinicalApi';

export const PatientsPage: FC = () => {
  const { patients, reload } = useClinicalData();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Form fields
  const [patientId, setPatientId] = useState('');
  const [age, setAge] = useState<number>(27);
  const [cohortLabel, setCohortLabel] = useState('Phenotype A (Classic PCOS - Hyperandrogenic, Anovulatory)');
  const [ethnicityTag, setEthnicityTag] = useState('asian_south_asian');
  const [notes, setNotes] = useState('');

  const filteredPatients = sortWorklist(
    patients.filter(
      (p) =>
        p.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.syntheticCohortLabel.toLowerCase().includes(searchTerm.toLowerCase()),
    ),
  );

  const handleCreatePatient = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const res = await ClinicalApiService.createPatient({
        id: patientId.trim() || undefined,
        age: Number(age),
        syntheticCohortLabel: cohortLabel,
        populationEthnicityTag: ethnicityTag,
        notes: notes.trim() || undefined,
      });

      await reload();
      setIsModalOpen(false);
      setPatientId('');
      setNotes('');
      if (res.patient_id) {
        navigate(`/patients/${encodeURIComponent(res.patient_id)}`);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create patient record.';
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

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
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
              {patients.length} records
            </span>
            <button
              type="button"
              onClick={() => {
                setErrorMessage(null);
                setIsModalOpen(true);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-700 hover:bg-teal-800 text-white text-xs font-medium rounded-md shadow-xs transition-colors cursor-pointer"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Log New Patient</span>
            </button>
          </div>
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
                  <th className="py-2.5 px-3">Patient ID</th>
                  <th className="py-2.5 px-3">Attention</th>
                  <th className="py-2.5 px-3">Cohort / Rotterdam Phenotype</th>
                  <th className="py-2.5 px-3 text-right">Age</th>
                  <th className="py-2.5 px-3 text-right">Visits</th>
                  <th className="py-2.5 px-3">Latest visit</th>
                  <th className="py-2.5 px-3">Completeness</th>
                  <th className="py-2.5 px-3 text-right">Meaningful shifts</th>
                  <th className="py-2.5 px-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredPatients.map((patient) => {
                  const attention = topAttention(patient);
                  const meaningfulShifts = meaningfulChangeCount(patient);
                  return (
                    <tr
                      key={patient.id}
                      onClick={() => navigate(`/patients/${encodeURIComponent(patient.id)}`)}
                      className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                    >
                      <td className="py-2.5 px-3 font-mono font-medium text-slate-900">
                        {patient.id}
                      </td>
                      <td className="py-2.5 px-3">
                        <AttentionBadge band={attention.band} />
                      </td>
                      <td className="py-2.5 px-3 text-slate-600 font-medium">
                        {patient.syntheticCohortLabel}
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-700">{patient.age}</td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-700">
                        {patient.totalVisits}
                      </td>
                      <td className="py-2.5 px-3 text-slate-600 whitespace-nowrap">
                        {patient.latestVisitDate || 'No visits recorded'}
                      </td>
                      <td className="py-2.5 px-3">
                        <DataCompleteness percentage={patient.dataCompleteness} size="sm" />
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-700">
                        {meaningfulShifts > 0 ? (
                          <span className="font-semibold text-amber-700">
                            +{meaningfulShifts}
                          </span>
                        ) : (
                          '0'
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-center text-slate-400">
                        <ChevronRight className="w-4 h-4 inline" />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal: Log New Patient */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white border border-slate-200 rounded-xl shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 bg-slate-50/70">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-teal-100 text-teal-800 rounded-lg">
                  <UserPlus className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 m-0">Log New Patient</h3>
                  <p className="text-[11px] text-slate-500 m-0">Section 5B De-identified Registration</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreatePatient} className="p-5 space-y-4">
              <div className="flex items-start gap-2 p-2.5 bg-amber-50 border border-amber-200 rounded-md text-[11px] text-amber-800">
                <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold">Clinical Privacy Guardrail:</span> Do not enter real patient names or personal identifying information. De-identified synthetic IDs only.
                </div>
              </div>

              {errorMessage && (
                <div className="flex items-center gap-2 p-2.5 bg-rose-50 border border-rose-200 rounded-md text-xs text-rose-700">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Patient ID <span className="text-slate-400 font-normal">(Optional)</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. P-0099"
                    value={patientId}
                    onChange={(e) => setPatientId(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-md font-mono focus:ring-1 focus:ring-teal-600 focus:outline-none"
                  />
                  <span className="text-[10px] text-slate-400">Leave blank for auto-generation</span>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Age in Years <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="90"
                    required
                    value={age}
                    onChange={(e) => setAge(Number(e.target.value))}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 focus:outline-none"
                  />
                  <span className="text-[10px] text-slate-400">Typical reproductive range: 12-55</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Rotterdam Phenotype / Cohort Tag <span className="text-rose-500">*</span>
                </label>
                <select
                  value={cohortLabel}
                  onChange={(e) => setCohortLabel(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 focus:outline-none"
                >
                  <option value="Phenotype A (Classic PCOS - Hyperandrogenic, Anovulatory)">
                    Phenotype A (Classic PCOS - Hyperandrogenic, Anovulatory, PCO)
                  </option>
                  <option value="Phenotype B (Metabolic-Dominant - Anovulatory & Hyperandrogenic)">
                    Phenotype B (Metabolic-Dominant - Anovulatory & Hyperandrogenic)
                  </option>
                  <option value="Phenotype C (Ovulatory PCOS - Hyperandrogenic, PCO Morphology)">
                    Phenotype C (Ovulatory PCOS - Regular Cycles, Psychological Burden)
                  </option>
                  <option value="Phenotype D (Non-Hyperandrogenic - Anovulatory & PCO Morphology)">
                    Phenotype D (Non-Hyperandrogenic - Normal Androgens, High LH:FSH)
                  </option>
                  <option value="Sparse / Longitudinal Validation Cohort">
                    Sparse / Longitudinal Validation Cohort
                  </option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Population / Ethnicity Profile
                </label>
                <select
                  value={ethnicityTag}
                  onChange={(e) => setEthnicityTag(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 focus:outline-none"
                >
                  <option value="asian_south_asian">
                    South Asian / Asian (IDF Criteria: Waist ≥80cm, BMI ≥23 Overweight, ≥27.5 Obese)
                  </option>
                  <option value="standard_who">
                    Standard WHO (Waist ≥88cm, BMI ≥25 Overweight, ≥30 Obese)
                  </option>
                </select>
                <span className="text-[10px] text-slate-500">Configures ethnicity-tailored metabolic thresholds</span>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Clinical Intake Notes <span className="text-slate-400 font-normal">(Optional)</span>
                </label>
                <textarea
                  rows={2}
                  placeholder="Baseline presentation, differential exclusions, or clinical context..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 focus:outline-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium rounded-md transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white text-xs font-medium rounded-md shadow-xs transition-colors cursor-pointer"
                >
                  {isSubmitting ? 'Registering...' : 'Register Patient'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
