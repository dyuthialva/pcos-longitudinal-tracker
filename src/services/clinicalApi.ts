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
const MAX_FAILED_ATTEMPTS = 5; {/* After 5 failed attempts, lockout for 1 minute */}
const LOCKOUT_MS = 60_000;    {/* 1 minute lockout after too many failed attempts */}

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
    throw new Error('Unable to complete the request. Try again.');
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
};
