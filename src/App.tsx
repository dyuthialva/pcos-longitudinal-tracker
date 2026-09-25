import { Navigate, Route, Routes } from 'react-router-dom';
import { RequireAuth } from './auth/RequireAuth';
import {
  ClinicalLayout,
  PatientRequiredOutlet,
} from './components/layout/ClinicalLayout';
import { LoginPage } from './pages/LoginPage';
import { PatientsPage } from './components/pages/PatientsPage';
import {
  OverviewRoute,
  VisitsRoute,
  TrendsRoute,
  EvidenceRoute,
} from './components/pages/PatientRoutes';

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <RequireAuth>
            <ClinicalLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/patients" replace />} />

        <Route path="/patients" element={<PatientsPage />} />

        <Route element={<PatientRequiredOutlet />}>
          <Route path="/patients/:patientId" element={<OverviewRoute />} />
          <Route path="/patients/:patientId/visits" element={<VisitsRoute />} />
          <Route path="/patients/:patientId/trends" element={<TrendsRoute />} />
          <Route path="/patients/:patientId/evidence" element={<EvidenceRoute />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/patients" replace />} />
    </Routes>
  );
}

export default App;