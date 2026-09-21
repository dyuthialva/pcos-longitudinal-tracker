import type { Patient, Visit, ParameterTrendPoint } from '../types/clinical';

import { MOCK_PATIENTS, extractParameterTrend } from '../data/mockPatients';

/**
 * Clinical Data Service Layer
 *
 * Designed as a clean abstraction so these asynchronous mock functions
 * can be replaced with real FastAPI `fetch('/api/...')` endpoints in production.
 */
export const ClinicalApiService = {
  async getAllPatients(): Promise<Patient[]> {
    // Simulated network latency
    return new Promise((resolve) => {
      setTimeout(() => resolve([...MOCK_PATIENTS]), 50);
    });
  },

  async getPatientById(patientId: string): Promise<Patient | null> {
    return new Promise((resolve) => {
      const patient = MOCK_PATIENTS.find((p) => p.id === patientId) || null;
      setTimeout(() => resolve(patient), 50);
    });
  },

  async getVisit(patientId: string, visitId: string): Promise<Visit | null> {
    return new Promise((resolve) => {
      const patient = MOCK_PATIENTS.find((p) => p.id === patientId);
      if (!patient) return resolve(null);
      const visit = patient.visits.find((v) => v.id === visitId) || null;
      setTimeout(() => resolve(visit), 50);
    });
  },

  async getParameterTrend(patientId: string, parameterName: string): Promise<ParameterTrendPoint[]> {
    return new Promise((resolve) => {
      const patient = MOCK_PATIENTS.find((p) => p.id === patientId);
      if (!patient) return resolve([]);
      const trends = extractParameterTrend(patient, parameterName);
      setTimeout(() => resolve(trends), 50);
    });
  },
};
