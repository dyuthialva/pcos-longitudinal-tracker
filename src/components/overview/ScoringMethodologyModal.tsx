import React from 'react';
import { X, Calculator, ShieldAlert } from 'lucide-react';


interface ScoringMethodologyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ScoringMethodologyModal: React.FC<ScoringMethodologyModalProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Calculator className="w-5 h-5 text-teal-400" />
            <div>
              <h3 className="text-base font-semibold text-white m-0">
                Scoring Methodology & Signal Composition
              </h3>
              <p className="text-xs text-slate-400 m-0">
                Domain-Level Clinical Decision Support
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 text-sm text-slate-700 max-h-[80vh] overflow-y-auto">
          {/* Mathematical Formula */}
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
            <h4 className="text-xs uppercase font-bold tracking-wider text-slate-500 mb-2">
              Domain Attention Score Formula
            </h4>
            <div className="font-mono text-sm bg-white p-3 rounded border border-slate-200 text-slate-900 font-semibold text-center">
              Score = (0.50 × Severity) + (0.30 × Trend) + (0.20 × Symptoms)
            </div>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Each domain attention score is scaled from 0 to 100 and represents the cumulative observational signal requiring clinician attention.
            </p>
          </div>

          {/* Component Breakdown */}
          <div className="space-y-3">
            <h4 className="text-xs uppercase font-bold tracking-wider text-slate-500">
              Component Definitions
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-3 rounded border border-slate-200 bg-white">
                <span className="text-xs font-bold text-teal-800 block">
                  0.50 × Severity
                </span>
                <p className="text-xs text-slate-600 mt-1">
                  Magnitude of deviation from validated clinical reference ranges at the current visit.
                </p>
              </div>

              <div className="p-3 rounded border border-slate-200 bg-white">
                <span className="text-xs font-bold text-indigo-800 block">
                  0.30 × Trend
                </span>
                <p className="text-xs text-slate-600 mt-1">
                  Longitudinal delta rate of change across sequential follow-up encounters.
                </p>
              </div>

              <div className="p-3 rounded border border-slate-200 bg-white">
                <span className="text-xs font-bold text-amber-800 block">
                  0.20 × Symptoms
                </span>
                <p className="text-xs text-slate-600 mt-1">
                  Validated patient-reported outcome measures and qualitative clinician logs.
                </p>
              </div>
            </div>
          </div>

          {/* Attention Bands */}
          <div className="space-y-2">
            <h4 className="text-xs uppercase font-bold tracking-wider text-slate-500">
              Score Attention Bands
            </h4>
            <div className="border border-slate-200 rounded-lg overflow-hidden text-xs">
              <div className="flex items-center justify-between p-2.5 bg-emerald-50/70 border-b border-slate-200">
                <span className="font-semibold text-emerald-900">Low (0 – 39)</span>
                <span className="text-emerald-800">Observations stable or within reference bounds.</span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-amber-50/70 border-b border-slate-200">
                <span className="font-semibold text-amber-900">Moderate (40 – 64)</span>
                <span className="text-amber-800">Emerging longitudinal shifts or borderline threshold markers.</span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-orange-50/70 border-b border-slate-200">
                <span className="font-semibold text-orange-900">Moderate-High (65 – 79)</span>
                <span className="text-orange-800">Multiple correlated parameters crossing surveillance thresholds.</span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-rose-50/70 border-b border-slate-200">
                <span className="font-semibold text-rose-900">High (80 – 100)</span>
                <span className="text-rose-800">Substantial acute or longitudinal shifts requiring clinician review.</span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-100">
                <span className="font-semibold text-slate-900">Insufficient Data</span>
                <span className="text-slate-600">Fewer than minimum required validated observations. Never default to low.</span>
              </div>
            </div>
          </div>

          {/* Boundaries Notice */}
          <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-900 flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
            <div>
              <strong className="font-semibold">Clinical Boundaries:</strong> This mathematical model does not calculate disease probability or risk scores. Attention scores exist solely to help prioritize clinical review of specific physiological domains.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-white bg-slate-900 rounded hover:bg-slate-800 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
