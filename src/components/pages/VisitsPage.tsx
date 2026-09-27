import React, { useState } from 'react';
import type { Patient } from '../../types/clinical';
import { DataCompleteness } from '../common/DataCompleteness';
import { Calendar, FileText, ChevronRight, PlusCircle, X, AlertCircle, CheckCircle2, Sparkles, FileSpreadsheet } from 'lucide-react';
import { useClinicalData } from '../../clinical/ClinicalDataContext';
import { ClinicalApiService } from '../../services/clinicalApi';

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
  const { reload } = useClinicalData();

  // Modal & Form State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Encounter info
  const todayStr = new Date().toISOString().split('T')[0];
  const [visitDate, setVisitDate] = useState(todayStr);
  const [sourceType, setSourceType] = useState('Comprehensive Clinical Encounter');
  const [notes, setNotes] = useState('');

  // Lab report extraction state
  const [labFile, setLabFile] = useState<File | null>(null);
  const [labRawText, setLabRawText] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionMsg, setExtractionMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [extractedLabs, setExtractedLabs] = useState<Array<{
    domain: string;
    parameter: string;
    value: string | number;
    unit: string;
    flag?: string | null;
  }>>([]);
  const [additionalObs, setAdditionalObs] = useState<Array<{
    domain: string;
    parameter: string;
    numeric_value?: number;
    text_value?: string;
    unit?: string;
  }>>([]);

  // Domain observations
  const [bmi, setBmi] = useState('');
  const [glucose, setGlucose] = useState('');
  const [hba1c, setHba1c] = useState('');
  const [cycleLength, setCycleLength] = useState('');
  const [missedPeriods, setMissedPeriods] = useState('');
  const [mfgScore, setMfgScore] = useState('');
  const [testosterone, setTestosterone] = useState('');
  const [phq9, setPhq9] = useState('');
  const [gad7, setGad7] = useState('');
  const [sleepHours, setSleepHours] = useState('');
  const [activityMin, setActivityMin] = useState('');

  // Sort visits newest first
  const sortedVisits = [...patient.visits].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  const latestVisitDate = sortedVisits.length > 0 ? sortedVisits[0].date : null;

  const handleExtractLab = async () => {
    if (!labFile && !labRawText.trim()) {
      setExtractionMsg({ text: 'Please select a lab report file (PDF) or paste report text to extract.', type: 'error' });
      return;
    }
    setIsExtracting(true);
    setExtractionMsg(null);
    try {
      const res = await ClinicalApiService.extractLabReport(labFile || undefined, labRawText.trim() || undefined);
      const items = res.extracted_values || (res.observations?.map(o => ({
        mapped_field: o.parameter,
        raw_label: o.parameter,
        value: o.numeric_value ?? (typeof o.value === 'number' ? o.value : parseFloat(String(o.value))),
        unit: o.unit,
        canonical_unit: o.unit,
        confidence: 'high',
        domain: o.domain,
        flag: o.flag,
      }))) || [];

      if (items.length === 0) {
        setExtractionMsg({ text: 'No clinical PCOS parameters detected in the provided report.', type: 'error' });
        setIsExtracting(false);
        return;
      }

      const extra: typeof additionalObs = [];
      const summary: typeof extractedLabs = [];

      items.forEach((item) => {
        const p = (item.mapped_field || item.raw_label || '').toLowerCase().replace(/\s+/g, '_');
        const numVal = item.value !== null && !isNaN(Number(item.value)) ? Number(item.value) : null;
        const unit = item.canonical_unit || item.unit || '';

        summary.push({
          domain: item.domain || 'Metabolic',
          parameter: (item.mapped_field || item.raw_label).replace(/_/g, ' '),
          value: numVal !== null ? numVal : (item.value ?? ''),
          unit,
          flag: item.flag,
        });

        if (p === 'fasting_glucose' || p === 'glucose' || p === 'fbs') {
          if (numVal !== null) setGlucose(String(numVal));
        } else if (p === 'hba1c') {
          if (numVal !== null) setHba1c(String(numVal));
        } else if (p === 'total_testosterone' || p === 'testosterone') {
          if (numVal !== null) setTestosterone(String(numVal));
        } else if (p === 'bmi') {
          if (numVal !== null) setBmi(String(numVal));
        } else if (p === 'cycle_length') {
          if (numVal !== null) setCycleLength(String(numVal));
        } else if (p === 'hirsutism_mfg_score' || p === 'mfg_score') {
          if (numVal !== null) setMfgScore(String(numVal));
        } else {
          extra.push({
            domain: item.domain || 'Metabolic',
            parameter: (item.mapped_field || item.raw_label).replace(/_/g, ' '),
            numeric_value: numVal !== null ? numVal : undefined,
            text_value: numVal === null ? String(item.value) : undefined,
            unit,
          });
        }
      });

      setExtractedLabs(summary);
      setAdditionalObs(extra);
      setExtractionMsg({
        text: `Extracted ${items.length} laboratory observation${items.length > 1 ? 's' : ''}. Verified fields populated below.`,
        type: 'success',
      });
    } catch (err: unknown) {
      setExtractionMsg({
        text: err instanceof Error ? err.message : 'Lab extraction failed. Please enter values manually.',
        type: 'error',
      });
    } finally {
      setIsExtracting(false);
    }
  };

  const handleCreateVisit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    // Build structured observations from non-empty inputs
    const observations: Array<{
      domain: string;
      parameter: string;
      numeric_value?: number;
      text_value?: string;
      unit?: string;
      measurement_status?: string;
    }> = [];

    // Include additional extracted lab observations
    if (additionalObs.length > 0) {
      observations.push(...additionalObs);
    }

    if (bmi.trim()) {
      observations.push({ domain: 'Metabolic', parameter: 'BMI', numeric_value: parseFloat(bmi), unit: 'kg/m2' });
    }
    if (glucose.trim()) {
      observations.push({ domain: 'Metabolic', parameter: 'Fasting Glucose', numeric_value: parseFloat(glucose), unit: 'mg/dL' });
    }
    if (hba1c.trim()) {
      observations.push({ domain: 'Metabolic', parameter: 'HbA1c', numeric_value: parseFloat(hba1c), unit: '%' });
    }
    if (cycleLength.trim()) {
      observations.push({ domain: 'Reproductive', parameter: 'Cycle Length', numeric_value: parseFloat(cycleLength), unit: 'days' });
    }
    if (missedPeriods.trim()) {
      observations.push({ domain: 'Reproductive', parameter: 'Missed Periods Count', numeric_value: parseFloat(missedPeriods), unit: 'periods' });
    }
    if (mfgScore.trim()) {
      observations.push({ domain: 'Hyperandrogenism', parameter: 'Hirsutism mFG Score', numeric_value: parseFloat(mfgScore), unit: 'points' });
    }
    if (testosterone.trim()) {
      observations.push({ domain: 'Hyperandrogenism', parameter: 'Total Testosterone', numeric_value: parseFloat(testosterone), unit: 'ng/mL' });
    }
    if (phq9.trim()) {
      observations.push({ domain: 'Psychological', parameter: 'PHQ-9 Score', numeric_value: parseFloat(phq9), unit: 'points' });
    }
    if (gad7.trim()) {
      observations.push({ domain: 'Psychological', parameter: 'GAD-7 Score', numeric_value: parseFloat(gad7), unit: 'points' });
    }
    if (sleepHours.trim()) {
      observations.push({ domain: 'Sleep', parameter: 'Sleep Hours', numeric_value: parseFloat(sleepHours), unit: 'hours' });
    }
    if (activityMin.trim()) {
      observations.push({ domain: 'Lifestyle', parameter: 'Activity Minutes Week', numeric_value: parseFloat(activityMin), unit: 'min/week' });
    }

    if (observations.length === 0 && !notes.trim()) {
      setErrorMessage('Please enter at least one clinical observation or clinical note to log a visit.');
      setIsSubmitting(false);
      return;
    }

    try {
      // 1. Create visit snapshot
      const created = await ClinicalApiService.createVisit(patient.id, {
        visit_date: visitDate,
        source_type: sourceType,
        free_text_notes: notes.trim() || undefined,
        observations,
      });

      // 2. Trigger downstream delta engine, scoring engine, and clinical narrative reasoning
      if (created.visit_id) {
        try {
          await ClinicalApiService.processVisit(patient.id, created.visit_id);
        } catch (procErr) {
          console.warn('Post-visit processing note:', procErr);
        }
      }

      await reload();
      setIsModalOpen(false);
      if (created.visit_id) {
        onSelectVisit(created.visit_id);
      }
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to log visit.');
    } finally {
      setIsSubmitting(false);
    }
  };

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

          <div className="flex items-center gap-3">
            <div className="text-xs font-mono text-slate-600 bg-slate-50 px-3 py-1.5 rounded border border-slate-200">
              {patient.totalVisits} Encounters Recorded
            </div>
            <button
              type="button"
              onClick={() => {
                setErrorMessage(null);
                setIsModalOpen(true);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold rounded-md shadow-xs transition-colors cursor-pointer"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Log New Visit</span>
            </button>
          </div>
        </div>
      </div>

      {/* Empty State when zero visits recorded */}
      {sortedVisits.length === 0 && (
        <div className="bg-white border border-dashed border-slate-300 rounded-lg p-10 text-center space-y-4">
          <Calendar className="w-10 h-10 text-slate-400 mx-auto" />
          <div>
            <h3 className="text-sm font-semibold text-slate-900">No Clinical Encounters Logged Yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              Log this patient's baseline encounter or lab snapshot to initiate longitudinal domain tracking, delta calculations, and clinical reasoning.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold rounded-md shadow-xs transition-colors cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Log Baseline Visit</span>
          </button>
        </div>
      )}

      {/* Visits Chronological List / Cards */}
      <div className="space-y-4">
        {sortedVisits.map((visit) => {
          const isSelected = visit.id === selectedVisitId;
          const meaningfulDeltas = visit.deltas.filter((d) => d.isMeaningful);
          const changedDomains = Array.from(new Set(meaningfulDeltas.map((d) => d.domain)));

          return (
            <div
              key={visit.id}
              className={`bg-white border rounded-lg p-5 transition-all shadow-xs ${isSelected
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
                    className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded transition ${isSelected
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
                <span>{visit.reasoningNarrative || 'No encounter narrative recorded.'}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal: Log New Visit */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-2xl my-8 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-teal-50 border border-teal-200 text-teal-700">
                  <Calendar className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 m-0">Log Clinical Encounter Snapshot</h3>
                  <p className="text-[11px] text-slate-500 m-0">
                    Patient <span className="font-mono font-semibold text-slate-700">{patient.id}</span> • Longitudinal visit tracking & automated scoring
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-md transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateVisit} className="p-6 space-y-5 max-h-[75vh] overflow-y-auto text-xs">
              {errorMessage && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-2 text-xs">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-600 text-[11px] flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-teal-600 shrink-0" />
                <span>
                  <strong>Clinical Decision Support Notice:</strong> Fill only the parameters measured during this encounter. Unmeasured fields are tracked cleanly as <em>NOT_MEASURED</em>.
                </span>
              </div>

              {/* Encounter Meta */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Encounter Date <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="date"
                    required
                    value={visitDate}
                    onChange={(e) => setVisitDate(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-teal-600 font-mono"
                  />
                  {latestVisitDate && (
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      Latest visit on record: {latestVisitDate}
                    </span>
                  )}
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Source / Encounter Type
                  </label>
                  <select
                    value={sourceType}
                    onChange={(e) => setSourceType(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-teal-600"
                  >
                    <option value="Comprehensive Clinical Encounter">Comprehensive Clinical Encounter</option>
                    <option value="Follow-up Lab Evaluation">Follow-up Lab Evaluation</option>
                    <option value="Endocrine Consultation">Endocrine Consultation</option>
                    <option value="Symptom Re-evaluation">Symptom Re-evaluation</option>
                    <option value="Telehealth Intake">Telehealth Intake</option>
                  </select>
                </div>
              </div>

              {/* Lab Report & Document Intake Section */}
              <div className="p-4 bg-teal-50/50 rounded-xl border border-teal-200 shadow-2xs space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileSpreadsheet className="w-4 h-4 text-teal-700" />
                    <span className="font-bold text-slate-900 text-xs">
                      Lab Report & Document Intake (OCR / Automated Extraction)
                    </span>
                  </div>
                  <span className="text-[10px] text-teal-800 font-semibold bg-teal-100 px-2 py-0.5 rounded border border-teal-200">
                    Auto-Extract
                  </span>
                </div>
                <p className="text-[11px] text-slate-600 m-0 leading-relaxed">
                  Upload a laboratory PDF report or paste raw test results. The extraction engine automatically maps lab aliases (e.g., FBS, S. Testosterone), normalizes units, and populates the clinical panels below.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  {/* File Upload */}
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1 text-[11px]">
                      Upload Lab PDF / Report Image
                    </label>
                    <input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg,.txt"
                      onChange={(e) => setLabFile(e.target.files?.[0] || null)}
                      className="text-[11px] text-slate-600 file:mr-2 file:py-1.5 file:px-3 file:rounded-md file:border file:border-slate-300 file:text-[11px] file:font-medium file:bg-white file:text-slate-700 hover:file:bg-slate-50 cursor-pointer w-full bg-white rounded-md border border-slate-200"
                    />
                  </div>

                  {/* Paste Text */}
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1 text-[11px]">
                      Or Paste Raw Lab Text
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. FBS 104 mg/dL, HbA1c 5.8%, Total Testosterone 0.78 ng/mL..."
                      value={labRawText}
                      onChange={(e) => setLabRawText(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 text-xs"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <button
                    type="button"
                    onClick={handleExtractLab}
                    disabled={isExtracting || (!labFile && !labRawText.trim())}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white font-semibold text-xs rounded-md shadow-xs transition-colors cursor-pointer"
                  >
                    {isExtracting ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>Extracting Lab Values...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Auto-Extract & Populate Panels</span>
                      </>
                    )}
                  </button>

                  {extractedLabs.length > 0 && (
                    <span className="text-[11px] font-semibold text-teal-800">
                      ✓ {extractedLabs.length} parameters extracted
                    </span>
                  )}
                </div>

                {extractionMsg && (
                  <div
                    className={`p-2.5 rounded-lg text-[11px] flex items-center gap-2 ${
                      extractionMsg.type === 'success'
                        ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
                        : 'bg-rose-50 border border-rose-200 text-rose-800'
                    }`}
                  >
                    {extractionMsg.type === 'success' ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    ) : (
                      <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                    )}
                    <span>{extractionMsg.text}</span>
                  </div>
                )}

                {/* Extracted Labs Chip List */}
                {extractedLabs.length > 0 && (
                  <div className="pt-2 border-t border-teal-200/60">
                    <span className="text-[10px] font-bold uppercase text-slate-500 block mb-1.5">
                      Extracted Parameters Preview:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {extractedLabs.map((lab, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-teal-300 text-slate-800 text-[11px] font-mono shadow-2xs"
                        >
                          <span className="font-sans text-slate-600 font-medium">{lab.parameter}:</span>
                          <span className="font-bold text-teal-900">{lab.value}</span>
                          <span className="text-slate-500 text-[10px]">{lab.unit}</span>
                          {lab.flag && (
                            <span className="text-[9px] font-bold text-amber-700 bg-amber-50 px-1 rounded border border-amber-200">
                              {lab.flag}
                            </span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Clinical Narrative / Notes */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Clinical Intake / Progress Notes
                </label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Patient reports irregular cycle (42 days), mild acne on jawline, and poor sleep quality..."
                  className="w-full px-3 py-2 bg-white border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-teal-600 resize-none"
                />
              </div>

              {/* Domain 1: Metabolic */}
              <div className="pt-2 border-t border-slate-200">
                <span className="font-semibold text-slate-800 uppercase tracking-wider text-[10px] text-teal-800 block mb-2">
                  Metabolic Domain
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-slate-600 mb-1">BMI (kg/m²)</label>
                    <input
                      type="number"
                      step="0.1"
                      placeholder="e.g. 26.4"
                      value={bmi}
                      onChange={(e) => setBmi(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-600 mb-1">Fasting Glucose (mg/dL)</label>
                    <input
                      type="number"
                      step="1"
                      placeholder="e.g. 96"
                      value={glucose}
                      onChange={(e) => setGlucose(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-600 mb-1">HbA1c (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      placeholder="e.g. 5.6"
                      value={hba1c}
                      onChange={(e) => setHba1c(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 font-mono"
                    />
                  </div>
                </div>
              </div>

              {/* Domain 2: Hyperandrogenism */}
              <div className="pt-2 border-t border-slate-200">
                <span className="font-semibold text-slate-800 uppercase tracking-wider text-[10px] text-teal-800 block mb-2">
                  Hyperandrogenism Domain
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-600 mb-1">Hirsutism mFG Score (0–36)</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      max="36"
                      placeholder="e.g. 9"
                      value={mfgScore}
                      onChange={(e) => setMfgScore(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-600 mb-1">Total Testosterone (ng/mL)</label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="e.g. 0.85"
                      value={testosterone}
                      onChange={(e) => setTestosterone(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 font-mono"
                    />
                  </div>
                </div>
              </div>

              {/* Domain 3: Reproductive */}
              <div className="pt-2 border-t border-slate-200">
                <span className="font-semibold text-slate-800 uppercase tracking-wider text-[10px] text-teal-800 block mb-2">
                  Reproductive Domain
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-600 mb-1">Cycle Length (days)</label>
                    <input
                      type="number"
                      step="1"
                      placeholder="e.g. 45"
                      value={cycleLength}
                      onChange={(e) => setCycleLength(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-600 mb-1">Missed Periods (past 12 mo)</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      max="12"
                      placeholder="e.g. 3"
                      value={missedPeriods}
                      onChange={(e) => setMissedPeriods(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 font-mono"
                    />
                  </div>
                </div>
              </div>

              {/* Domain 4 & 5: Psychological, Sleep & Lifestyle */}
              <div className="pt-2 border-t border-slate-200">
                <span className="font-semibold text-slate-800 uppercase tracking-wider text-[10px] text-teal-800 block mb-2">
                  Psychological, Lifestyle & Sleep Domains
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="block text-slate-600 mb-1">PHQ-9 (0–27)</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      max="27"
                      placeholder="e.g. 6"
                      value={phq9}
                      onChange={(e) => setPhq9(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-600 mb-1">GAD-7 (0–21)</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      max="21"
                      placeholder="e.g. 4"
                      value={gad7}
                      onChange={(e) => setGad7(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-600 mb-1">Sleep (hrs/night)</label>
                    <input
                      type="number"
                      step="0.5"
                      placeholder="e.g. 6.5"
                      value={sleepHours}
                      onChange={(e) => setSleepHours(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-600 mb-1">Activity (min/wk)</label>
                    <input
                      type="number"
                      step="10"
                      placeholder="e.g. 90"
                      value={activityMin}
                      onChange={(e) => setActivityMin(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 font-mono"
                    />
                  </div>
                </div>
              </div>

              {/* Form Action Buttons */}
              <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  disabled={isSubmitting}
                  className="px-4 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium rounded-md transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white font-semibold rounded-md shadow-xs transition-colors cursor-pointer"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Saving & Computing Scores...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Save & Process Encounter</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

