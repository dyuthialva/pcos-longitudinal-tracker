import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { Patient } from '../types/clinical';
import { ClinicalApiService } from '../services/clinicalApi';
import { useAuth } from '../auth/AuthContext';

interface ClinicalDataValue {
  patients: Patient[];
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  selectedVisitId: (patientId: string) => string;
  setVisitForPatient: (patientId: string, visitId: string) => void;
}

const ClinicalDataContext = createContext<ClinicalDataValue | null>(null);

export function ClinicalDataProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [visitByPatient, setVisitByPatient] = useState<Record<string, string>>({});

  const reload = useCallback(async () => {
    if (!isAuthenticated) {
      setPatients([]);
      setVisitByPatient({});
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const list = await ClinicalApiService.listPatients();
      setPatients(list);
      setVisitByPatient((current) => {
        const next = { ...current };
        for (const patient of list) {
          if (!next[patient.id] && patient.visits[0]) {
            next[patient.id] = patient.visits[0].id;
          }
        }
        return next;
      });
    } catch (err) {
      setPatients([]);
      setError(err instanceof Error ? err.message : 'Unable to load patient records.');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const value = useMemo<ClinicalDataValue>(
    () => ({
      patients,
      loading,
      error,
      reload,
      selectedVisitId: (patientId: string) => {
        const stored = visitByPatient[patientId];
        if (stored) return stored;
        return patients.find((p) => p.id === patientId)?.visits[0]?.id ?? '';
      },
      setVisitForPatient: (patientId, visitId) => {
        setVisitByPatient((current) => ({ ...current, [patientId]: visitId }));
      },
    }),
    [error, loading, patients, reload, visitByPatient],
  );

  return <ClinicalDataContext.Provider value={value}>{children}</ClinicalDataContext.Provider>;
}

export function useClinicalData(): ClinicalDataValue {
  const ctx = useContext(ClinicalDataContext);
  if (!ctx) {
    throw new Error('useClinicalData must be used within ClinicalDataProvider');
  }
  return ctx;
}
