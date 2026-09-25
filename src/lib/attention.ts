import type { AttentionBand, DomainScore, DomainType, Patient, Visit } from '../types/clinical';

const BAND_RANK: Record<AttentionBand, number> = {
  High: 4,
  'Moderate-High': 3,
  Moderate: 2,
  Low: 1,
  'Insufficient Data': 0,
};

const CANONICAL_DOMAINS: DomainType[] = [
  'Reproductive',
  'Hyperandrogenism',
  'Metabolic',
  'Lifestyle',
  'Psychological',
  'Sleep',
];

export function bandRank(band: AttentionBand): number {
  return BAND_RANK[band] ?? 0;
}

export function latestVisit(patient: Patient): Visit | undefined {
  return [...patient.visits].sort((a, b) => b.visitNumber - a.visitNumber)[0];
}

export function domainScoresForVisit(visit: Visit): DomainScore[] {
  return CANONICAL_DOMAINS.map((domain) => {
    return (
      visit.domainScores[domain] || {
        domain,
        score: null,
        band: 'Insufficient Data' as const,
        severityComponent: null,
        trendComponent: null,
        symptomsComponent: null,
        isInsufficientData: true,
        insufficientReason: 'No observation records found for this domain.',
        contributingParameters: [],
        meaningfulDeltasCount: 0,
        observationCount: 0,
      }
    );
  });
}

/** Highest-attention scored domain first; insufficient data last. */
export function rankedDomainScores(visit: Visit): DomainScore[] {
  return [...domainScoresForVisit(visit)].sort((a, b) => {
    if (a.isInsufficientData !== b.isInsufficientData) {
      return a.isInsufficientData ? 1 : -1;
    }
    const scoreDelta = (b.score ?? -1) - (a.score ?? -1);
    if (scoreDelta !== 0) return scoreDelta;
    return bandRank(b.band) - bandRank(a.band);
  });
}

export function topAttention(patient: Patient): {
  domain: DomainType | null;
  band: AttentionBand;
  score: number | null;
} {
  const visit = latestVisit(patient);
  if (!visit) {
    return { domain: null, band: 'Insufficient Data', score: null };
  }
  const ranked = rankedDomainScores(visit);
  const top = ranked.find((d) => !d.isInsufficientData) ?? ranked[0];
  return {
    domain: top?.domain ?? null,
    band: top?.band ?? 'Insufficient Data',
    score: top?.score ?? null,
  };
}

export function parseVisitDate(value: string): number {
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

export function sortWorklist(patients: Patient[]): Patient[] {
  return [...patients].sort((a, b) => {
    const aTop = topAttention(a);
    const bTop = topAttention(b);
    const bandDelta = bandRank(bTop.band) - bandRank(aTop.band);
    if (bandDelta !== 0) return bandDelta;
    const recency = parseVisitDate(b.latestVisitDate) - parseVisitDate(a.latestVisitDate);
    if (recency !== 0) return recency;
    return b.dataCompleteness - a.dataCompleteness;
  });
}

export function meaningfulChangeCount(patient: Patient): number {
  const visit = latestVisit(patient);
  if (!visit) return 0;
  return visit.deltas.filter((d) => d.isMeaningful).length;
}
