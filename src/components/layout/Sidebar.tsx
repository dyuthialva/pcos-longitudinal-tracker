import { type FC } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  Users,
  CalendarDays,
  LineChart,
  FileSpreadsheet,
  ShieldCheck,
  Stethoscope,
  LogOut,
} from 'lucide-react';
import type { Patient } from '../../types/clinical';
import { useAuth } from '../../auth/AuthContext';
import type { NavSection } from './nav';

interface SidebarProps {
  currentSection: NavSection;
  activePatient: Patient | null;
  patients: Patient[];
  onSelectPatient: (patientId: string) => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: FC<SidebarProps> = ({
  currentSection,
  activePatient,
  patients,
  onSelectPatient,
  isMobileOpen = false,
  onCloseMobile,
}) => {
  const { doctor, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const patientBase = activePatient ? `/patients/${activePatient.id}` : '/patients';

  const navItems: Array<{ id: NavSection; label: string; to: string; icon: typeof Activity; badge?: string }> = [
    { id: 'overview', label: 'Overview', to: patientBase, icon: Activity },
    { id: 'patients', label: 'Worklist', to: '/patients', icon: Users, badge: `${patients.length}` },
    {
      id: 'visits',
      label: 'Visits',
      to: `${patientBase}/visits`,
      icon: CalendarDays,
      badge: activePatient ? `${activePatient.visits.length}` : undefined,
    },
    { id: 'trends', label: 'Trends', to: `${patientBase}/trends`, icon: LineChart },
    { id: 'evidence', label: 'Evidence', to: `${patientBase}/evidence`, icon: FileSpreadsheet },
  ];

  const handleNavClick = (to: string, section: NavSection) => {
    if (section !== 'patients' && !activePatient) {
      navigate('/patients');
    } else {
      navigate(to);
    }
    onCloseMobile?.();
  };

  return (
    <>
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-40 lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-slate-900 text-slate-200 border-r border-slate-800 flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-5 border-b border-slate-800/80">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-600/90 text-white flex items-center justify-center font-bold shadow-xs">
              <Stethoscope className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-base font-semibold tracking-tight text-white m-0 leading-tight">
                PCOS Tracker
              </h1>
              <p className="text-[11px] font-normal text-teal-400/90 tracking-wide mt-0.5">
                Clinician workspace
              </p>
            </div>
          </div>
        </div>

        <div className="px-4 py-3 border-b border-slate-800/60 bg-slate-950/40">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Active patient
            </span>
            {activePatient && (
              <span className="text-[10px] text-teal-400 font-mono">{activePatient.id}</span>
            )}
          </div>
          <select
            value={activePatient?.id ?? ''}
            onChange={(e) => {
              if (e.target.value) onSelectPatient(e.target.value);
            }}
            className="w-full bg-slate-800 text-xs text-slate-100 rounded border border-slate-700 px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-teal-500 font-mono"
          >
            <option value="" disabled>
              Select a patient
            </option>
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.id} • {p.totalVisits} visits ({p.dataCompleteness}%)
              </option>
            ))}
          </select>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 px-3 mb-2">
            Navigation
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.id === 'patients'
                ? location.pathname === '/patients'
                : currentSection === item.id && Boolean(activePatient);
            return (
              <NavLink
                key={item.id}
                to={item.id !== 'patients' && !activePatient ? '/patients' : item.to}
                onClick={(e) => {
                  e.preventDefault();
                  handleNavClick(item.to, item.id);
                }}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition ${
                  isActive
                    ? 'bg-teal-700/80 text-white font-semibold shadow-xs'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-teal-200' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge ? (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                      isActive ? 'bg-teal-900/60 text-teal-100' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {item.badge}
                  </span>
                ) : null}
              </NavLink>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800/80 bg-slate-950/60 space-y-2.5">
          <div className="text-[11px] text-slate-300">
            <p className="font-semibold m-0">{doctor?.name}</p>
            <p className="text-slate-500 font-mono m-0 truncate">{doctor?.email}</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-2 h-2 rounded-full bg-teal-400" />
            <span className="text-[11px] font-medium text-slate-300">Prototype • Synthetic data</span>
          </div>
          <div className="rounded border border-teal-900/60 bg-teal-950/40 p-2.5">
            <div className="flex items-start gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-[11px] font-semibold text-teal-200 leading-tight">
                  Decision support only
                </p>
                <p className="text-[10px] text-slate-400 mt-1 leading-snug">
                  Observational trends and domain attention signals. Non-diagnostic.
                </p>
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => void logout()}
            className="w-full inline-flex items-center justify-center gap-2 text-xs font-medium text-slate-200 border border-slate-700 rounded-md py-1.5 hover:bg-slate-800"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign out
          </button>
        </div>
      </aside>
    </>
  );
};
