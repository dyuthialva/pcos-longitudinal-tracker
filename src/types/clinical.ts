export type DomainType =
  | 'Reproductive'
  | 'Hyperandrogenism'
  | 'Metabolic'
  | 'Lifestyle'
  | 'Psychological'
  | 'Sleep';

export type AttentionBand =
  | 'Low'
  | 'Moderate'
  | 'Moderate-High'
  | 'High'
  | 'Insufficient Data';

export type ObservationSource =
  | 'Self report'
  | 'Lab report'
  | 'Clinician entry'
  | 'Computed';

export type ObservationFlag =
  | 'normal'
  | 'borderline'
  | 'elevated'
  | 'low'
  | 'abnormal';

export interface Observation {
  id: string;
  domain: DomainType;
  parameter: string;
  value: number | string;
  numericValue?: number;
  unit: string;
  date: string;
  source: ObservationSource;
  visitId: string;
  referenceRange?: string;
  flag?: ObservationFlag;
  notes?: string;
}

export interface ClinicalDelta {
  id: string;
  domain: DomainType;
  parameter: string;
  previousValue: number | string | null;
  currentValue: number | string;
  deltaDisplay: string;
  numericDelta?: number;
  unit: string;
  direction: 'up' | 'down' | 'neutral' | 'changed';
  statusTag: 'Threshold crossed' | 'Moderate change' | 'Substantial shift' | 'Stable' | 'New observation' | 'Attention required';
  statusSeverity: 'neutral' | 'moderate' | 'high';
  isMeaningful: boolean;
  clinicalNote?: string;
}

export interface DomainScore {
  domain: DomainType;
  score: number | null; // null if insufficient data
  band: AttentionBand;
  severityComponent: number | null; // 0-100
  trendComponent: number | null;    // 0-100
  symptomsComponent: number | null; // 0-100
  isInsufficientData: boolean;
  insufficientReason?: string;
  contributingParameters: string[];
  meaningfulDeltasCount: number;
  observationCount: number;
}

export interface Visit {
  id: string;
  visitNumber: number;
  date: string;
  sourceType: string;
  totalObservations: number;
  meaningfulChangesCount: number;
  dataCompleteness: number; // 0-100 percentage
  reasoningNarrative: string; // Clinical context narrative strictly adhering to decision-support bounds
  domainScores: Record<DomainType, DomainScore>;
  deltas: ClinicalDelta[];
  observations: Observation[];
}

export interface Patient {
  id: string; // e.g. "P-0042"
  syntheticCohortLabel: string;
  age: number;
  firstVisitDate: string;
  latestVisitDate: string;
  totalVisits: number;
  dataCompleteness: number; // 0-100 percentage
  lastUpdated: string;
  notes?: string;
  visits: Visit[];
}

export interface ParameterTrendPoint {
  visitDate: string;
  visitId: string;
  visitNumber: number;
  value: number;
  displayValue: string;
  unit: string;
  source: ObservationSource;
  flag?: ObservationFlag;
  referenceMin?: number;
  referenceMax?: number;
}
