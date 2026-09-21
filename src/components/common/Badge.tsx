import React from 'react';
import type { AttentionBand, ObservationFlag } from '../../types/clinical';

import { AlertCircle, AlertTriangle, CheckCircle2, HelpCircle, ShieldAlert } from 'lucide-react';

interface AttentionBadgeProps {
  band: AttentionBand;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const AttentionBadge: React.FC<AttentionBadgeProps> = ({
  band,
  size = 'md',
  showIcon = true,
}) => {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs font-medium px-2.5 py-1 gap-1.5',
    lg: 'text-sm font-semibold px-3 py-1.5 gap-2',
  };

  switch (band) {
    case 'Low':
      return (
        <span
          className={`inline-flex items-center rounded-md border border-emerald-200 bg-emerald-50/80 text-emerald-800 ${sizeClasses[size]}`}
          title="Low domain attention signal"
        >
          {showIcon && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
          <span>Low</span>
        </span>
      );

    case 'Moderate':
      return (
        <span
          className={`inline-flex items-center rounded-md border border-amber-200 bg-amber-50/90 text-amber-800 ${sizeClasses[size]}`}
          title="Moderate domain attention signal"
        >
          {showIcon && <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />}
          <span>Moderate</span>
        </span>
      );

    case 'Moderate-High':
      return (
        <span
          className={`inline-flex items-center rounded-md border border-orange-200 bg-orange-50/90 text-orange-800 ${sizeClasses[size]}`}
          title="Moderate-High domain attention signal"
        >
          {showIcon && <AlertCircle className="w-3.5 h-3.5 text-orange-600" />}
          <span>Moderate-High</span>
        </span>
      );

    case 'High':
      return (
        <span
          className={`inline-flex items-center rounded-md border border-rose-200 bg-rose-50/90 text-rose-800 ${sizeClasses[size]}`}
          title="High domain attention signal"
        >
          {showIcon && <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />}
          <span>High</span>
        </span>
      );

    case 'Insufficient Data':
    default:
      return (
        <span
          className={`inline-flex items-center rounded-md border border-dashed border-slate-300 bg-slate-100 text-slate-700 ${sizeClasses[size]}`}
          title="Insufficient validated observations available"
        >
          {showIcon && <HelpCircle className="w-3.5 h-3.5 text-slate-500" />}
          <span>Insufficient Data</span>
        </span>
      );
  }
};

interface FlagBadgeProps {
  flag?: ObservationFlag;
}

export const FlagBadge: React.FC<FlagBadgeProps> = ({ flag }) => {
  if (!flag || flag === 'normal') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-normal bg-slate-100 text-slate-600">
        Normal
      </span>
    );
  }

  if (flag === 'borderline') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
        Borderline
      </span>
    );
  }

  if (flag === 'elevated' || flag === 'abnormal') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">
        {flag === 'elevated' ? 'Elevated' : 'Abnormal'}
      </span>
    );
  }

  if (flag === 'low') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
        Low
      </span>
    );
  }

  return null;
};

interface StatusTagProps {
  status: string;
  severity?: 'neutral' | 'moderate' | 'high';
}

export const StatusTag: React.FC<StatusTagProps> = ({ status, severity = 'neutral' }) => {
  const styles = {
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
    moderate: 'bg-amber-50 text-amber-800 border-amber-200',
    high: 'bg-rose-50 text-rose-800 border-rose-200 font-medium',
  };

  return (
    <span className={`inline-flex items-center text-xs px-2 py-0.5 rounded border ${styles[severity]}`}>
      {status}
    </span>
  );
};
