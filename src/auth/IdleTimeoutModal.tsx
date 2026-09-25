import { AlertTriangle } from 'lucide-react';

interface IdleTimeoutModalProps {
  open: boolean;
  onStay: () => void;
  onSignOut: () => void;
}

export function IdleTimeoutModal({ open, onStay, onSignOut }: IdleTimeoutModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[80] bg-slate-900/50 flex items-center justify-center p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="idle-title"
        className="w-full max-w-md bg-white rounded-lg border border-slate-200 shadow-lg p-5"
      >
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-md bg-amber-50 text-amber-700">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h2 id="idle-title" className="text-base font-semibold text-slate-900 m-0">
              Session about to expire
            </h2>
            <p className="text-sm text-slate-600 mt-2 leading-relaxed">
              No activity was detected for several minutes. You will be signed out to protect patient records.
            </p>
          </div>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onSignOut}
            className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded hover:bg-slate-50"
          >
            Sign out now
          </button>
          <button
            type="button"
            onClick={onStay}
            className="px-3 py-1.5 text-xs font-semibold text-white bg-teal-700 rounded hover:bg-teal-800"
          >
            Stay signed in
          </button>
        </div>
      </div>
    </div>
  );
}
