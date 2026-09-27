import { type FC } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { Patient, Visit } from '../../types/clinical';
import { useClinicalData } from '../../clinical/ClinicalDataContext';
import { EmptyState } from '../common/EmptyState';
import { OverviewPage } from './OverviewPage';
import { VisitsPage } from './VisitsPage';
import { TrendsPage } from './TrendsPage';
import { EvidencePage } from './EvidencePage';

function usePatientChart(): {
  patient: Patient | null;
  selectedVisit: Visit | null;
  onSelectVisit: (visitId: string) => void;
} {
  const { patientId } = useParams();
  const { patients, selectedVisitId, setVisitForPatient } = useClinicalData();
  const patient = patients.find((p) => p.id === patientId) ?? null;
  const visitId = patient ? selectedVisitId(patient.id) : '';
  const selectedVisit = patient?.visits.find((v) => v.id === visitId) ?? patient?.visits[0] ?? null;
  return {
    patient,
    selectedVisit,
    onSelectVisit: (id: string) => {
      if (patient) setVisitForPatient(patient.id, id);
    },
  };
}

export const OverviewRoute: FC = () => {
  const navigate = useNavigate();
  const { patient, selectedVisit, onSelectVisit } = usePatientChart();
  if (!patient) return <EmptyState title="Patient not found" description="Unable to find this record." />;
  if (!selectedVisit) {
    return (
      <div className="bg-white border border-slate-200 rounded-lg p-8 max-w-lg mx-auto text-center space-y-4 my-8 shadow-xs">
        <h3 className="text-base font-semibold text-slate-900">No Visits Recorded Yet</h3>
        <p className="text-xs text-slate-500">
          Patient {patient.id} has been registered, but has no clinical encounters logged yet.
        </p>
        <button
          onClick={() => navigate(`/patients/${patient.id}/visits`)}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold rounded-md shadow-xs cursor-pointer transition-colors"
        >
          Log Initial Encounter
        </button>
      </div>
    );
  }
  return (
    <OverviewPage
      patient={patient}
      selectedVisit={selectedVisit}
      onSelectVisit={onSelectVisit}
      onNavigateToEvidence={() => navigate(`/patients/${patient.id}/evidence`)}
    />
  );
};

export const VisitsRoute: FC = () => {
  const navigate = useNavigate();
  const { patient, selectedVisit, onSelectVisit } = usePatientChart();
  if (!patient) return <EmptyState title="Patient not found" description="Unable to find this patient." />;
  return (
    <VisitsPage
      patient={patient}
      selectedVisitId={selectedVisit?.id || ''}
      onSelectVisit={onSelectVisit}
      onNavigateToOverview={() => navigate(`/patients/${patient.id}`)}
    />
  );
};

export const TrendsRoute: FC = () => {
  const { patient } = usePatientChart();
  if (!patient) return <EmptyState title="Patient not found" description="Unable to load trends for this identifier." />;
  return <TrendsPage patient={patient} />;
};

export const EvidenceRoute: FC = () => {
  const { patient, selectedVisit, onSelectVisit } = usePatientChart();
  if (!patient || !selectedVisit) return <EmptyState title="No visit selected" description="This record has no visits yet." />;
  return (
    <EvidencePage patient={patient} selectedVisit={selectedVisit} onSelectVisit={onSelectVisit} />
  );
};
