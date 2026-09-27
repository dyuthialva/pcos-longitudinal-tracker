import type { Patient, Visit, ParameterTrendPoint } from '../types/clinical';
import type { AuthSession, DoctorProfile } from '../types/auth';
import { extractParameterTrend, MOCK_PATIENTS } from '../data/mockPatients';

const TOKEN_STORAGE_KEY = 'pcos.session.token';
const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? '';

const MOCK_DOCTORS: Array<DoctorProfile & { password: string }> = [
  {
    id: 'doc-mehta',
    name: 'Dr. A. Mehta',
    email: 'dr.mehta@clinic.local',
    role: 'doctor',
    password: 'ClinicianDemo!2026',
  },
  {
    id: 'doc-rao',
    name: 'Dr. S. Rao',
    email: 'dr.rao@clinic.local',
    role: 'doctor',
    password: 'ClinicianDemo!2026',
  },
];

const MOCK_DELAY_MS = 80;
const MAX_FAILED_ATTEMPTS = 5; {/* After 5 failed attempts, lockout for 1 minute */ }
const LOCKOUT_MS = 60_000; {/* 1 minute lockout after too many failed attempts */ }

type UnauthorizedHandler = () => void;

let onUnauthorized: UnauthorizedHandler | null = null;
let memoryToken: string | null = null;
const issuedTokens = new Map<string, DoctorProfile>();
const failedAttempts = new Map<string, { count: number; lockedUntil: number }>();

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), MOCK_DELAY_MS);
  });
}

function persistToken(token: string | null): void {
  memoryToken = token;
  if (token) {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

function readStoredToken(): string | null {
  if (memoryToken) return memoryToken;
  try {
    const stored = sessionStorage.getItem(TOKEN_STORAGE_KEY);
    memoryToken = stored;
    return stored;
  } catch {
    return null;
  }
}

function useLiveApi(): boolean {
  return Boolean(API_BASE);
}

function authHeaders(): HeadersInit {
  const token = readStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function liveRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
  });

  if (response.status === 401) {
    persistToken(null);
    onUnauthorized?.();
    throw new Error('Session expired. Please sign in again.');
  }

  if (!response.ok) {
    let errorDetail = 'Unable to complete the request. Try again.';
    try {
      const errorJson = await response.json();
      if (errorJson && errorJson.detail) {
        if (typeof errorJson.detail === 'string') {
          errorDetail = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          errorDetail = errorJson.detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
        }
      }
    } catch {
      // fallback to status text
      if (response.statusText) errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function requireMockAuth(): DoctorProfile {
  const token = readStoredToken();
  if (!token) {
    onUnauthorized?.();
    throw new Error('Not authenticated.');
  }
  const doctor = doctorFromToken(token);
  if (!doctor) {
    persistToken(null);
    onUnauthorized?.();
    throw new Error('Session expired. Please sign in again.');
  }
  return doctor;
}

function mockLogin(email: string, password: string): AuthSession {
  const normalized = email.trim().toLowerCase();
  const now = Date.now();
  const attempt = failedAttempts.get(normalized);

  if (attempt && attempt.lockedUntil > now) {
    throw new Error('Too many attempts. Try again in a minute.');
  }

  const doctor = MOCK_DOCTORS.find((d) => d.email === normalized && d.password === password);
  if (!doctor) {
    const nextCount = (attempt?.count ?? 0) + 1;
    failedAttempts.set(normalized, {
      count: nextCount,
      lockedUntil: nextCount >= MAX_FAILED_ATTEMPTS ? now + LOCKOUT_MS : 0,
    });
    if (nextCount >= MAX_FAILED_ATTEMPTS) {
      throw new Error('Too many attempts. Try again in a minute.');
    }
    throw new Error('Invalid credentials.');
  }

  failedAttempts.delete(normalized);
  const profile: DoctorProfile = {
    id: doctor.id,
    name: doctor.name,
    email: doctor.email,
    role: doctor.role,
  };
  const token = `mock.${profile.id}.${crypto.randomUUID()}`;
  issuedTokens.set(token, profile);
  persistToken(token);
  return { token, doctor: profile };
}

function doctorFromToken(token: string): DoctorProfile | null {
  const cached = issuedTokens.get(token);
  if (cached) return cached;
  const parts = token.split('.');
  if (parts[0] !== 'mock' || !parts[1]) return null;
  const seed = MOCK_DOCTORS.find((d) => d.id === parts[1]);
  if (!seed) return null;
  const profile: DoctorProfile = {
    id: seed.id,
    name: seed.name,
    email: seed.email,
    role: seed.role,
  };
  issuedTokens.set(token, profile);
  return profile;
}

export const ClinicalApiService = {
  setUnauthorizedHandler(handler: UnauthorizedHandler | null) {
    onUnauthorized = handler;
  },

  getStoredToken(): string | null {
    return readStoredToken();
  },

  async login(email: string, password: string): Promise<AuthSession> {
    if (useLiveApi()) {
      const session = await liveRequest<AuthSession>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      persistToken(session.token);
      return session;
    }
    return delay(mockLogin(email, password));
  },

  async logout(): Promise<void> {
    const token = readStoredToken();
    try {
      if (useLiveApi() && token) {
        await liveRequest<void>('/api/auth/logout', { method: 'POST' });
      }
    } finally {
      if (token) issuedTokens.delete(token);
      persistToken(null);
    }
  },

  async getSession(): Promise<AuthSession | null> {
    const token = readStoredToken();
    if (!token) return null;

    if (useLiveApi()) {
      try {
        const doctor = await liveRequest<DoctorProfile>('/api/auth/me');
        return { token, doctor };
      } catch {
        persistToken(null);
        return null;
      }
    }

    const doctor = doctorFromToken(token);
    if (!doctor) {
      persistToken(null);
      return null;
    }
    return delay({ token, doctor });
  },

  async listPatients(): Promise<Patient[]> {
    if (useLiveApi()) {
      return liveRequest<Patient[]>('/api/patients');
    }
    requireMockAuth();
    return delay(MOCK_PATIENTS.map((p) => ({ ...p })));
  },

  async createPatient(data: {
    id?: string;
    syntheticCohortLabel: string;
    age: number;
    populationEthnicityTag?: string;
    notes?: string;
  }): Promise<{ patient_id: string; synthetic_cohort_label: string; age: number }> {
    if (useLiveApi()) {
      return liveRequest('/api/v1/patients', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    }
    requireMockAuth();
    const pid = data.id || `P-${MOCK_PATIENTS.length + 101}`;
    const newPat: Patient = {
      id: pid,
      syntheticCohortLabel: data.syntheticCohortLabel,
      age: data.age,
      firstVisitDate: '27 Sep 2026',
      latestVisitDate: '27 Sep 2026',
      totalVisits: 0,
      dataCompleteness: 100,
      lastUpdated: '27 Sep 2026',
      notes: data.notes,
      visits: [],
    };
    MOCK_PATIENTS.unshift(newPat);
    return delay({ patient_id: pid, synthetic_cohort_label: data.syntheticCohortLabel, age: data.age });
  },

  async getPatient(patientId: string): Promise<Patient | null> {
    if (useLiveApi()) {
      return liveRequest<Patient>(`/api/patients/${encodeURIComponent(patientId)}`);
    }
    requireMockAuth();
    const patient = MOCK_PATIENTS.find((p) => p.id === patientId) || null;
    return delay(patient ? { ...patient } : null);
  },

  async getVisit(patientId: string, visitId: string): Promise<Visit | null> {
    if (useLiveApi()) {
      return liveRequest<Visit>(
        `/api/patients/${encodeURIComponent(patientId)}/visits/${encodeURIComponent(visitId)}`,
      );
    }
    requireMockAuth();
    const patient = MOCK_PATIENTS.find((p) => p.id === patientId);
    if (!patient) return delay(null);
    const visit = patient.visits.find((v) => v.id === visitId) || null;
    return delay(visit ?? null);
  },

  async getParameterTrend(
    patientId: string,
    parameterName: string,
  ): Promise<ParameterTrendPoint[]> {
    if (useLiveApi()) {
      const qs = new URLSearchParams({ parameter: parameterName });
      return liveRequest<ParameterTrendPoint[]>(
        `/api/patients/${encodeURIComponent(patientId)}/trends?${qs.toString()}`,
      );
    }
    requireMockAuth();
    const patient = MOCK_PATIENTS.find((p) => p.id === patientId);
    if (!patient) return delay([]);
    return delay(extractParameterTrend(patient, parameterName));
  },

  async createVisit(
    patientId: string,
    data: {
      visit_date: string;
      source_type?: string;
      free_text_notes?: string;
      observations: Array<{
        domain: string;
        parameter: string;
        numeric_value?: number;
        text_value?: string;
        unit?: string;
        measurement_status?: string;
      }>;
    }
  ): Promise<{ visit_id: string; visit_number: number; visit_date: string }> {
    if (useLiveApi()) {
      return liveRequest(`/api/v1/patients/${encodeURIComponent(patientId)}/visits`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    }
    requireMockAuth();
    return delay({
      visit_id: `v${Date.now()}-${patientId}`,
      visit_number: 1,
      visit_date: data.visit_date,
    });
  },

  async processVisit(patientId: string, visitId: string): Promise<Visit> {
    if (useLiveApi()) {
      return liveRequest(`/api/v1/patients/${encodeURIComponent(patientId)}/visits/${encodeURIComponent(visitId)}/process`, {
        method: 'POST',
      });
    }
    requireMockAuth();
    throw new Error('Process visit requires live API.');
  },

  async extractLabReport(file?: File, rawText?: string): Promise<{
    extraction_id?: string;
    source_method: string;
    confidence: string;
    needs_clinician_review: boolean;
    extracted_values?: Array<{
      mapped_field?: string;
      raw_label: string;
      value: number | null;
      unit: string;
      canonical_unit: string;
      original_value?: number | string;
      confidence: string;
      domain?: string;
      flag?: string | null;
    }>;
    unmapped_lines?: Array<{ raw_label: string; raw_value: string }>;
    flagged_for_review?: Array<{ mapped_field?: string; reason: string }>;
    observations?: Array<{
      domain: string;
      parameter: string;
      value: number | string;
      numeric_value: number | null;
      unit: string;
      flag?: string | null;
    }>;
  }> {
    if (useLiveApi()) {
      const formData = new FormData();
      if (file) {
        formData.append('file', file);
      }
      if (rawText) {
        formData.append('raw_text', rawText);
      }

      const token = readStoredToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/api/v1/extraction/lab-pdf`, {
        method: 'POST',
        headers,
        body: formData,
      });

      if (!response.ok) {
        let errDetail = 'Failed to extract lab report.';
        try {
          const j = await response.json();
          if (j.detail) errDetail = j.detail;
        } catch {
          // ignore
        }
        throw new Error(errDetail);
      }

      return response.json();
    }

    return delay({
      source_method: 'free_text',
      confidence: 'high',
      needs_clinician_review: false,
      extracted_values: [
        { mapped_field: 'fasting_glucose', raw_label: 'Fasting Glucose', value: 96, unit: 'mg/dL', canonical_unit: 'mg/dL', confidence: 'high', domain: 'Metabolic' },
        { mapped_field: 'hba1c', raw_label: 'HbA1c', value: 5.5, unit: '%', canonical_unit: '%', confidence: 'high', domain: 'Metabolic' },
        { mapped_field: 'total_testosterone', raw_label: 'Total Testosterone', value: 0.65, unit: 'ng/mL', canonical_unit: 'ng/mL', confidence: 'high', domain: 'Hyperandrogenism' },
      ],
    });
  },
};

