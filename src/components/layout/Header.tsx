import { type FC } from 'react';
import { Menu, Stethoscope } from 'lucide-react';
import type { Patient } from '../../types/clinical';
import { useAuth } from '../../auth/AuthContext';

interface HeaderProps {
  activePatient: Patient | null;
  onOpenMobileMenu: () => void;
}

export const Header: FC<HeaderProps> = ({ activePatient, onOpenMobileMenu }) => {
  const { doctor } = useAuth();

  return (
    <header className="bg-white border-b border-slate-200 px-4 py-3 sm:px-6 lg:hidden flex items-center justify-between sticky top-0 z-30 shadow-xs">
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileMenu}
          className="p-1.5 rounded-md text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:outline-none"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-teal-700 text-white flex items-center justify-center font-bold">
            <Stethoscope className="w-3.5 h-3.5" />
          </div>
          <span className="font-semibold text-slate-900 text-sm">PCOS Tracker</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {activePatient && (
          <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
            {activePatient.id}
          </span>
        )}
        <span className="text-[11px] text-slate-500 hidden sm:inline">{doctor?.name}</span>
      </div>
    </header>
  );
};
