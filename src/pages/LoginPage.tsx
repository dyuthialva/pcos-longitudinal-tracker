import { useState, type FormEvent } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Lock, Stethoscope, ShieldCheck } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';

export function LoginPage() {
  const { isReady, isAuthenticated, login } = useAuth();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from || '/patients';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (isReady && isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      <div className="hidden lg:flex w-[46%] flex-col justify-between p-10 border-r border-slate-800 bg-[radial-gradient(circle_at_top_left,_rgba(13,148,136,0.18),_transparent_42%)]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-teal-600 text-white flex items-center justify-center">
            <Stethoscope className="w-5 h-5" />
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight m-0">PCOS Tracker</p>
            <p className="text-[11px] text-teal-300/90 m-0">Clinician workspace</p>
          </div>
        </div>
        <div className="max-w-md space-y-4">
          <h1 className="text-3xl font-semibold tracking-tight text-white m-0 leading-tight">
            Longitudinal attention signals for PCOS follow-up.
          </h1>
          <p className="text-sm text-slate-400 leading-relaxed">
            Authorized clinicians only. This workspace surfaces domain-level changes, evidence, and
            decision-support context. It does not diagnose or recommend treatment.
          </p>
        </div>
        <p className="text-[11px] text-slate-500 flex items-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
          Prototype authentication — production requires server-side sessions.
        </p>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 sm:p-10 bg-slate-50 text-slate-900">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-lg bg-teal-700 text-white flex items-center justify-center">
              <Stethoscope className="w-4 h-4" />
            </div>
            <span className="font-semibold text-slate-900">PCOS Tracker</span>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
            <div className="flex items-center gap-2 mb-1">
              <Lock className="w-4 h-4 text-teal-700" />
              <h2 className="text-lg font-semibold m-0">Clinician sign in</h2>
            </div>
            <p className="text-xs text-slate-500 mb-5">
              No public registration. Access is limited to issued clinician accounts.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4" autoComplete="on">
              <div>
                <label htmlFor="email" className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-teal-600"
                />
              </div>
              <div>
                <label htmlFor="password" className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-teal-600"
                />
              </div>

              {error && (
                <p className="text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2" role="alert">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2.5 text-sm font-semibold text-white bg-teal-700 rounded-md hover:bg-teal-800 disabled:opacity-60"
              >
                {submitting ? 'Signing in…' : 'Sign in'}
              </button>
            </form>
          </div>

          <p className="mt-4 text-[11px] text-slate-500 leading-relaxed">
            Demo clinicians (synthetic data only): <span className="font-mono">dr.mehta@clinic.local</span> or{' '}
            <span className="font-mono">dr.rao@clinic.local</span> / <span className="font-mono">ClinicianDemo!2026</span>
          </p>
          <p className="mt-2 text-[11px] text-slate-400">Non-diagnostic decision support. Authorized use only.</p>
        </div>
      </div>
    </div>
  );
}
