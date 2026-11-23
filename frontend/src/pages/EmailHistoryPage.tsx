import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { historyApi } from '../api/history';
import { smtpAccountsApi } from '../api/smtpAccounts';
import type { EmailJob, SMTPAccount, PaginatedResponse } from '../types';
import { formatDate, statusColor, cn } from '../utils';
import { toast } from 'sonner';
import { Search, Filter, ChevronRight, History } from 'lucide-react';

const STATUSES = ['', 'PENDING', 'PROCESSING', 'ACCEPTED', 'FAILED', 'RETRYING', 'CANCELLED'];

export default function EmailHistoryPage() {
  const [data, setData] = useState<PaginatedResponse<EmailJob>>({ items: [], total: 0, page: 1, per_page: 20, pages: 0 });
  const [accounts, setAccounts] = useState<SMTPAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ search: '', status: '', smtp_account_id: '', date_from: '', date_to: '' });
  const [page, setPage] = useState(1);

  const load = async (pg = page) => {
    try {
      const params: Record<string, string | number> = { page: pg, per_page: 20 };
      if (filters.search) params.search = filters.search;
      if (filters.status) params.status = filters.status;
      if (filters.smtp_account_id) params.smtp_account_id = filters.smtp_account_id;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;
      const { data: res } = await historyApi.list(params);
      setData(res);
    } catch { toast.error('Failed to load history'); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    smtpAccountsApi.list().then(r => setAccounts(r.data)).catch(() => {});
  }, []);

  useEffect(() => { load(page); }, [page, filters]);

  const setFilter = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFilters(f => ({ ...f, [k]: e.target.value }));
    setPage(1);
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Email History</h1>
        <p className="text-gray-500 text-sm mt-1">{data.total} email job{data.total !== 1 ? 's' : ''} found</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input value={filters.search} onChange={setFilter('search')} placeholder="Search subject..."
            className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-48" />
        </div>
        <select value={filters.status} onChange={setFilter('status')} className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
          {STATUSES.map(s => <option key={s} value={s}>{s || 'All Statuses'}</option>)}
        </select>
        <select value={filters.smtp_account_id} onChange={setFilter('smtp_account_id')} className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option value="">All Accounts</option>
          {accounts.map(a => <option key={a.id} value={a.id}>{a.account_name}</option>)}
        </select>
        <input type="date" value={filters.date_from} onChange={setFilter('date_from')} className="border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        <input type="date" value={filters.date_to} onChange={setFilter('date_to')} className="border border-gray-300 rounded-lg px-3 py-2 text-sm" />
      </div>

      {data.items.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-16 text-center">
          <History className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-sm">No emails found. <Link to="/compose" className="text-blue-600">Send your first email →</Link></p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                {['Subject', 'Recipients', 'SMTP Account', 'Submitted', 'Status', 'Retries', ''].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {data.items.map(job => {
                const acc = accounts.find(a => a.id === job.smtp_account_id);
                return (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 max-w-xs">
                      <p className="font-medium text-gray-900 truncate">{job.subject}</p>
                      <p className="text-xs text-gray-400 font-mono">{job.id.slice(0, 8)}...</p>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{job.recipient_count}</td>
                    <td className="px-4 py-3 text-gray-600 text-xs">{acc?.account_name || '—'}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(job.created_at)}</td>
                    <td className="px-4 py-3">
                      <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', statusColor(job.status))}>{job.status}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{job.retry_count}/{job.max_retries}</td>
                    <td className="px-4 py-3">
                      <Link to={`/history/${job.id}`} className="text-blue-600 hover:text-blue-800">
                        <ChevronRight className="h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {data.pages > 1 && (
            <div className="p-4 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
              <span>Page {data.page} of {data.pages} · {data.total} total</span>
              <div className="flex gap-2">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={data.page <= 1} className="px-3 py-1 border rounded disabled:opacity-40 hover:bg-gray-50">Prev</button>
                <button onClick={() => setPage(p => Math.min(data.pages, p + 1))} disabled={data.page >= data.pages} className="px-3 py-1 border rounded disabled:opacity-40 hover:bg-gray-50">Next</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
