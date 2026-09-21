import { useState, useEffect } from 'react';

import { MOCK_PATIENTS } from './data/mockPatients';
import type { Patient, Visit } from './types/clinical';
import { Sidebar, type NavSection } from './components/layout/Sidebar';
import { DisclaimerBanner } from './components/layout/DisclaimerBanner';
import { Header } from './components/layout/Header';
import { OverviewPage } from './components/pages/OverviewPage';
import { PatientsPage } from './components/pages/PatientsPage';
import { VisitsPage } from './components/pages/VisitsPage';
import { TrendsPage } from './components/pages/TrendsPage';
import { EvidencePage } from './components/pages/EvidencePage';
import { ShieldCheck } from 'lucide-react';


export function App() {
  const [patients] = useState<Patient[]>(MOCK_PATIENTS);
  const [activePatientId, setActivePatientId] = useState<string>('P-0042');
  const [currentSection, setCurrentSection] = useState<NavSection>('overview');
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  const activePatient =
    patients.find((p) => p.id === activePatientId) || patients[0];

  // Store selected visit ID per patient or default to latest visit
  const [selectedVisitId, setSelectedVisitId] = useState<string>(
    activePatient.visits[0]?.id || ''
  );

  // Keep selected visit valid whenever active patient changes
  useEffect(() => {
    if (activePatient && activePatient.visits.length > 0) {
      setSelectedVisitId(activePatient.visits[0].id);
    }
  }, [activePatientId]);

  const selectedVisit: Visit =
    activePatient.visits.find((v) => v.id === selectedVisitId) ||
    activePatient.visits[0];

  const handleSelectPatient = (patientId: string) => {
    setActivePatientId(patientId);
  };

  const handleSelectVisit = (visitId: string) => {
    setSelectedVisitId(visitId);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col">
      {/* Top Disclaimer Banner */}
      <DisclaimerBanner />

      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Fixed / Collapsible Sidebar */}
        <Sidebar
          currentSection={currentSection}
          onSelectSection={setCurrentSection}
          activePatient={activePatient}
          patients={patients}
          onSelectPatient={handleSelectPatient}
          isMobileOpen={mobileMenuOpen}
          onCloseMobile={() => setMobileMenuOpen(false)}
        />

        {/* Mobile Header */}
        <Header
          activePatient={activePatient}
          onOpenMobileMenu={() => setMobileMenuOpen(true)}
        />

        {/* Main Content Area */}
        <main className="flex-1 lg:ml-64 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {currentSection === 'overview' && (
            <OverviewPage
              patient={activePatient}
              selectedVisit={selectedVisit}
              onSelectVisit={handleSelectVisit}
              onNavigateToEvidence={() => setCurrentSection('evidence')}
            />
          )}

          {currentSection === 'patients' && (
            <PatientsPage
              patients={patients}
              activePatientId={activePatient.id}
              onSelectPatient={(pid) => {
                handleSelectPatient(pid);
                setCurrentSection('overview');
              }}
            />
          )}

          {currentSection === 'visits' && (
            <VisitsPage
              patient={activePatient}
              selectedVisitId={selectedVisit.id}
              onSelectVisit={handleSelectVisit}
              onNavigateToOverview={() => setCurrentSection('overview')}
            />
          )}

          {currentSection === 'trends' && (
            <TrendsPage patient={activePatient} />
          )}

          {currentSection === 'evidence' && (
            <EvidencePage
              patient={activePatient}
              selectedVisit={selectedVisit}
              onSelectVisit={handleSelectVisit}
            />
          )}

          {/* Footer Decision Support Disclaimer */}
          <footer className="mt-12 pt-6 border-t border-slate-200 text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-teal-700" />
              <span>
                <strong>PCOS Longitudinal Decision Support</strong> • Prototype for clinical research & provider decision-support.
              </span>
            </div>
            <div className="font-mono text-[11px] text-slate-400">
              Non-Diagnostic • Traceable Observational Evidence
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}

export default App;
