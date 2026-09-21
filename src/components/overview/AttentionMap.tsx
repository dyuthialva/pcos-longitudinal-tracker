import React, { useState } from 'react';
import type { DomainType, Visit } from '../../types/clinical';
import { AttentionDomain } from './AttentionDomain';
import { ScoringMethodologyModal } from './ScoringMethodologyModal';
import { HelpCircle } from 'lucide-react';


interface AttentionMapProps {
  visit: Visit;
  onSelectDomain: (domain: DomainType) => void;
}

export const AttentionMap: React.FC<AttentionMapProps> = ({ visit, onSelectDomain }) => {
  const [showMethodology, setShowMethodology] = useState(false);

  // Maintain canonical domain ordering
  const orderedDomains: DomainType[] = [
    'Reproductive',
    'Hyperandrogenism',
    'Metabolic',
    'Lifestyle',
    'Psychological',
    'Sleep',
  ];

  return (
    <section className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-slate-900 m-0">
              Attention Map
            </h2>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
              6 Clinical Domains
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Domain-level signals calculated from observed severity, trend, and symptoms.
          </p>
        </div>

        <button
          onClick={() => setShowMethodology(true)}
          className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-2.5 py-1.5 rounded transition shrink-0 self-start sm:self-auto"
        >
          <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
          <span>Scoring methodology</span>
        </button>
      </div>

      <div className="space-y-3 mt-4">
        {orderedDomains.map((domain) => {
          const scoreData = visit.domainScores[domain] || {
            domain,
            score: null,
            band: 'Insufficient Data',
            severityComponent: null,
            trendComponent: null,
            symptomsComponent: null,
            isInsufficientData: true,
            insufficientReason: 'No observation records found for this domain.',
            contributingParameters: [],
            meaningfulDeltasCount: 0,
            observationCount: 0,
          };

          return (
            <AttentionDomain
              key={domain}
              scoreData={scoreData}
              onClick={() => onSelectDomain(domain)}
            />
          );
        })}
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <span className="italic">
          Click any domain card to view parameter trend curves and raw traceable evidence.
        </span>
        <span className="hidden sm:inline-block font-mono text-[11px]">
          Score range: 0 (Baseline) – 100 (High Attention)
        </span>
      </div>

      <ScoringMethodologyModal
        isOpen={showMethodology}
        onClose={() => setShowMethodology(false)}
      />
    </section>
  );
};
