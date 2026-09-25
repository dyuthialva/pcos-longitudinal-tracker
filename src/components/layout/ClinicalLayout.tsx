import { useState } from 'react';
import { Outlet, useLocation, useNavigate, useParams } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { DisclaimerBanner } from './DisclaimerBanner';
import { IdleTimeoutModal } from '../../auth/IdleTimeoutModal';
import { useAuth } from '../../auth/AuthContext';
import { useClinicalData } from '../../clinical/ClinicalDataContext';
import { LoadingSkeleton } from '../common/LoadingSkeleton';
import { EmptyState } from '../common/EmptyState';
import type { NavSection } from './nav';

function sectionFromPath(pathname: string): NavSection {
  if (pathname === '/patients') return 'patients';
  if (pathname.endsWith('/visits')) return 'visits';
  if (pathname.endsWith('/trends')) return 'trends';
  if (pathname.endsWith('/evidence')) return 'evidence';
  return 'overview';
}

export function ClinicalLayout() {
  const { patientId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { idleWarning, staySignedIn, logout, doctor } = useAuth();
  const { patients, loading, error, reload } = useClinicalData();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const activePatient = patients.find((p) => p.id === patientId) ?? null;
  const currentSection = sectionFromPath(location.pathname);

  const handleSelectPatient = (id: string) => {
    const suffix =
      currentSection === 'patients' || currentSection === 'overview' ? '' : `/${currentSection}`;
    navigate(`/patients/${id}${suffix}`);
    setMobileMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col">
      <DisclaimerBanner />
      <IdleTimeoutModal
        open={idleWarning}
        onStay={staySignedIn}
        onSignOut={() => void logout()}
      />

      <div className="flex-1 flex flex-col lg:flex-row">
        <Sidebar
          currentSection={currentSection}
          activePatient={activePatient}
          patients={patients}
          onSelectPatient={handleSelectPatient}
          isMobileOpen={mobileMenuOpen}
          onCloseMobile={() => setMobileMenuOpen(false)}
        />

        <Header
          activePatient={activePatient}
          onOpenMobileMenu={() => setMobileMenuOpen(true)}
        />

        <main className="flex-1 lg:ml-64 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <div className="hidden lg:flex items-center justify-between mb-4 pb-3 border-b border-slate-200">
            <div className="flex items-center gap-3 text-xs text-slate-600">
              <span className="font-semibold text-slate-900">{doctor?.name}</span>
              <span className="text-slate-300">•</span>
              <span>{activePatient ? `Patient ${activePatient.id}` : 'Worklist'}</span>
              {activePatient && (
                <>
                  <span className="text-slate-300">•</span>
                  <span>Latest visit {activePatient.latestVisitDate}</span>
                </>
              )}
            </div>
            <span className="text-[11px] font-mono text-slate-400">Authorized clinician session</span>
          </div>

          {loading ? (
            <LoadingSkeleton rows={6} />
          ) : error ? (
            <EmptyState
              title="Unable to load records"
              description={error}
              actionText="Retry"
              onAction={() => void reload()}
            />
          ) : (
            <Outlet />
          )}

          <footer className="mt-12 pt-6 border-t border-slate-200 text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-teal-700" />
              <span>
                <strong>PCOS Longitudinal Decision Support</strong> • Clinician workspace. Decision
                support only.
              </span>
            </div>
            <div className="font-mono text-[11px] text-slate-400">
              Non-diagnostic • Traceable observational evidence
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}

export function PatientRequiredOutlet() {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const { patients, loading } = useClinicalData();

  if (loading) return null;
  const patient = patients.find((p) => p.id === patientId);
  if (!patient) {
    return (
      <EmptyState
        title="Patient not found"
        description="This identifier is not in your current worklist, or you are not authorized to view it."
        actionText="Back to worklist"
        onAction={() => navigate('/patients')}
      />
    );
  }

  return <Outlet />;
}

