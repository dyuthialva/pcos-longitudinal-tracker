import React, { useState } from 'react';
import type { DomainType, Patient, Visit } from '../../types/clinical';

import { PatientHeader } from '../overview/PatientHeader';
import { ChangesList } from '../overview/ChangesList';
import { AttentionMap } from '../overview/AttentionMap';
import { ReasoningCard } from '../overview/ReasoningCard';
import { TrendChart } from '../trends/TrendChart';
import { EvidenceTable } from '../evidence/EvidenceTable';
import { DomainDetailModal } from '../detail/DomainDetailModal';
import { WhatChangedStrip } from '../overview/WhatChangedStrip';

interface OverviewPageProps {
  patient: Patient;
  selectedVisit: Visit;
  onSelectVisit: (visitId: string) => void;
  onNavigateToEvidence: () => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  patient,
  selectedVisit,
  onSelectVisit,
  onNavigateToEvidence,
}) => {
  const [activeDrillDownDomain, setActiveDrillDownDomain] = useState<DomainType | null>(null);

  return (
    <div className="space-y-6 pb-12">
      {/* Patient Header with Visit Selector */}
      <PatientHeader
  patient={patient}
  selectedVisit={selectedVisit}
  onSelectVisit={onSelectVisit}
/>

<WhatChangedStrip
  visit={selectedVisit}
  onSelectDomain={(domain) => setActiveDrillDownDomain(domain as DomainType)}
/>
      {/*Two changes done:
          1.Changed the Overview two-column breakpoint from lg to xl to prevent desktop content from being squeezed
          2.Added min-w-0 to grid columns so cards and text stay within their allocated width*/}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        <div className="xl:col-span-7 space-y-6">       
          {/* Section 1: Changes Since Previous Visit */}
          <ChangesList
            visit={selectedVisit}
            onViewAllObservations={onNavigateToEvidence}
            onDrillDownDomain={(domainStr) => setActiveDrillDownDomain(domainStr as DomainType)}
          />
          {/* Section 2: Attention Map */}
          <AttentionMap
            visit={selectedVisit}
            onSelectDomain={(dom) => setActiveDrillDownDomain(dom)}
          />
        </div>

        <div className="xl:col-span-5 space-y-6">
          {/* Section 4: Clinical Context Reasoning Card */}
          <ReasoningCard visit={selectedVisit} />

          {/* Section 6: Longitudinal Trends Chart */}
          <TrendChart patient={patient} initialParameter="Weight" />
        </div>
      </div>

      {/* Section 7: Raw Evidence Drill-Down for Current Visit */}
      <div className="pt-2">
        <EvidenceTable
          observations={selectedVisit.observations}
          visit={selectedVisit}
        />
      </div>

      {/* Domain Detail Modal (Section 3) */}
      <DomainDetailModal
        domain={activeDrillDownDomain}
        patient={patient}
        visit={selectedVisit}
        onClose={() => setActiveDrillDownDomain(null)}
      />
    </div>
  );
};
