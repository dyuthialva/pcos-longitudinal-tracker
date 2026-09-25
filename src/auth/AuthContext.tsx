import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { DoctorProfile } from '../types/auth';
import { ClinicalApiService } from '../services/clinicalApi';

const IDLE_MS = 15 * 60 * 1000;
const WARN_BEFORE_MS = 2 * 60 * 1000;
const ACTIVITY_EVENTS: Array<keyof WindowEventMap> = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'];

interface AuthContextValue {
  doctor: DoctorProfile | null;
  isReady: boolean;
  isAuthenticated: boolean;
  idleWarning: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  staySignedIn: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [doctor, setDoctor] = useState<DoctorProfile | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [idleWarning, setIdleWarning] = useState(false);
  const lastActivityRef = useRef(Date.now());
  const idleTimerRef = useRef<number | null>(null);
  const warnTimerRef = useRef<number | null>(null);

  const clearIdleTimers = () => {
    if (idleTimerRef.current) window.clearTimeout(idleTimerRef.current);
    if (warnTimerRef.current) window.clearTimeout(warnTimerRef.current);
    idleTimerRef.current = null;
    warnTimerRef.current = null;
  };

  const logout = useCallback(async () => {
    clearIdleTimers();
    setIdleWarning(false);
    setDoctor(null);
    await ClinicalApiService.logout();
  }, []);

  const scheduleIdle = useCallback(() => {
    clearIdleTimers();
    setIdleWarning(false);
    lastActivityRef.current = Date.now();
    warnTimerRef.current = window.setTimeout(() => {
      setIdleWarning(true);
    }, IDLE_MS - WARN_BEFORE_MS);
    idleTimerRef.current = window.setTimeout(() => {
      void logout();
    }, IDLE_MS);
  }, [logout]);

  const staySignedIn = useCallback(() => {
    scheduleIdle();
  }, [scheduleIdle]);

  const login = useCallback(
    async (email: string, password: string) => {
      const session = await ClinicalApiService.login(email, password);
      setDoctor(session.doctor);
      scheduleIdle();
    },
    [scheduleIdle],
  );

  useEffect(() => {
    ClinicalApiService.setUnauthorizedHandler(() => {
      setDoctor(null);
      setIdleWarning(false);
      clearIdleTimers();
    });

    let cancelled = false;
    void ClinicalApiService.getSession().then((session) => {
      if (cancelled) return;
      if (session) {
        setDoctor(session.doctor);
        scheduleIdle();
      }
      setIsReady(true);
    });

    return () => {
      cancelled = true;
      ClinicalApiService.setUnauthorizedHandler(null);
    };
  }, [scheduleIdle]);

  useEffect(() => {
    if (!doctor) {
      clearIdleTimers();
      return;
    }

    const onActivity = () => {
      if (Date.now() - lastActivityRef.current < 1000) return;
      if (!idleWarning) {
        scheduleIdle();
      }
    };

    ACTIVITY_EVENTS.forEach((event) => window.addEventListener(event, onActivity, { passive: true }));
    return () => {
      ACTIVITY_EVENTS.forEach((event) => window.removeEventListener(event, onActivity));
    };
  }, [doctor, idleWarning, scheduleIdle]);

  const value = useMemo<AuthContextValue>(
    () => ({
      doctor,
      isReady,
      isAuthenticated: Boolean(doctor),
      idleWarning,
      login,
      logout,
      staySignedIn,
    }),
    [doctor, idleWarning, isReady, login, logout, staySignedIn],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
