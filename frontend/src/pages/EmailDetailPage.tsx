import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { emailsApi } from '../api/emails';
import type { EmailDetail } from '../types';
import { formatDate, statusColor, cn } from '../utils';
import { toast } from 'sonner';
import { ArrowLeft, RefreshCw, XCircle, AlertTriangle, CheckCircle, Clock, Loader2 } from 'lucide-react';

export default function EmailDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<EmailDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [retrying, setRetrying] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  const load = async () => {
    if (!id) return;
    try {
      const { data } = await emailsApi.get(id);
      setDetail(data);
    } catch { toast.error('Failed to load email details'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [id]);

  const handleRetry = async () => {
    if (!id) return;
    setRetrying(true);
    try {
      await emailsApi.retry(id);
      toast.success('Email queued for retry');
      await load();
    } catch { toast.error('Failed to retry email'); }
    finally { setRetrying(false); }
  };

  const handleCancel = async () => {
    if (!id || !confirm('Cancel this email job?')) return;
    setCancelling(true);
    try {
      await emailsApi.cancel(id);
      toast.success('Email cancelled');
      await load();
    } catch { toast.error('Failed to cancel email'); }
    finally { setCancelling(false); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;
  if (!detail) return <div className="text-center py-16 text-gray-400">Email not found.</div>;

  const { job, recipients, attempts } = detail;

  return (
    <div className="max-w-3xl space-y-6">
      <button onClick={() => navigate('/history')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900">
        <ArrowLeft className="h-4 w-4" /> Back to History
      </button>

      {/* Job Info */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-900 truncate">{job.subject}</h1>
            <p className="text-xs text-gray-400 font-mono mt-0.5">Job {job.id}</p>
          </div>
          <span className={cn('px-3 py-1 rounded-full text-sm font-medium', statusColor(job.status))}>{job.status}</span>
        </div>
        <div className="p-5 grid grid-cols-2 gap-4 text-sm">
          <div><p className="text-gray-500 text-xs mb-0.5">Sender</p><p className="font-medium">{job.sender_name ? `${job.sender_name} <${job.sender_email}>` : job.sender_email}</p></div>
          <div><p className="text-gray-500 text-xs mb-0.5">Recipients</p><p className="font-medium">{job.recipient_count} recipient{job.recipient_count !== 1 ? 's' : ''}</p></div>
          <div><p className="text-gray-500 text-xs mb-0.5">Submitted</p><p>{formatDate(job.created_at)}</p></div>
          <div><p className="text-gray-500 text-xs mb-0.5">Completed</p><p>{formatDate(job.completed_at)}</p></div>
          <div><p className="text-gray-500 text-xs mb-0.5">Message Type</p><p className="capitalize">{job.message_type}</p></div>
          <div><p className="text-gray-500 text-xs mb-0.5">Retries</p><p>{job.retry_count} / {job.max_retries}</p></div>
          {job.last_error && (
            <div className="col-span-2">
              <p className="text-gray-500 text-xs mb-0.5">Last Error</p>
              <p className="text-red-700 bg-red-50 px-3 py-2 rounded text-xs font-mono">{job.last_error}</p>
            </div>
          )}
        </div>

        {/* Important SMTP note */}
        <div className="mx-5 mb-5 flex items-start gap-2 p-3 bg-amber-50 border border-amber-100 rounded-lg text-xs text-amber-800">
          <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <span><strong>Note:</strong> "Accepted" means the SMTP server accepted the message for delivery. It does not confirm the email reached the recipient's inbox.</span>
        </div>

        {/* Actions */}
        <div className="px-5 pb-5 flex gap-3">
          {job.status === 'FAILED' && (
            <button onClick={handleRetry} disabled={retrying}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-60">
              {retrying ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />} Retry
            </button>
          )}
          {['PENDING', 'RETRYING'].includes(job.status) && (
            <button onClick={handleCancel} disabled={cancelling}
              className="flex items-center gap-2 border border-red-300 text-red-600 px-4 py-2 rounded-lg text-sm hover:bg-red-50 disabled:opacity-60">
              {cancelling ? <Loader2 className="h-4 w-4 animate-spin" /> : <XCircle className="h-4 w-4" />} Cancel
            </button>
          )}
        </div>
      </div>

      {/* Recipients */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-4 border-b border-gray-100"><h2 className="font-semibold text-gray-900">Recipients</h2></div>
        <div className="divide-y divide-gray-50">
          {recipients.map(r => (
            <div key={r.id} className="px-5 py-3 flex items-center justify-between text-sm">
              <div>
                <span className="uppercase text-xs font-medium text-gray-400 mr-2">{r.recipient_type}</span>
                <span className="text-gray-900">{r.recipient_name ? `${r.recipient_name} <${r.recipient_email}>` : r.recipient_email}</span>
              </div>
              <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium',
                r.status === 'ACCEPTED' ? 'bg-green-50 text-green-700' :
                r.status === 'FAILED' ? 'bg-red-50 text-red-700' : 'bg-gray-100 text-gray-600'
              )}>{r.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Attempts */}
      {attempts.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="p-4 border-b border-gray-100"><h2 className="font-semibold text-gray-900">Sending Attempts</h2></div>
          <div className="divide-y divide-gray-50">
            {attempts.map(a => (
              <div key={a.id} className="px-5 py-4">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    {a.status === 'success' ? <CheckCircle className="h-4 w-4 text-green-600" /> : <XCircle className="h-4 w-4 text-red-600" />}
                    <span className="font-medium text-sm text-gray-900">Attempt #{a.attempt_number}</span>
                    {a.smtp_response_code && <span className="text-xs bg-gray-100 px-2 py-0.5 rounded font-mono">Code {a.smtp_response_code}</span>}
                  </div>
                  <span className="text-xs text-gray-400">{formatDate(a.attempted_at)}</span>
                </div>
                {a.smtp_response_message && <p className="text-xs text-green-700 bg-green-50 px-3 py-1.5 rounded font-mono mt-1">{a.smtp_response_message}</p>}
                {a.error_message && <p className="text-xs text-red-700 bg-red-50 px-3 py-1.5 rounded font-mono mt-1">{a.error_message}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
