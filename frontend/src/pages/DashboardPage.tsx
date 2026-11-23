import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line,
} from 'recharts';
import { Mail, CheckCircle, XCircle, Clock, RefreshCw, Server, Users, FileText, TrendingUp } from 'lucide-react';
import { dashboardApi } from '../api/dashboard';
import { historyApi } from '../api/history';
import type { DashboardSummary, EmailTrendPoint, AccountPerformance, EmailJob } from '../types';
import { formatRelative, statusColor, cn } from '../utils';
import { toast } from 'sonner';

const COLORS = ['#22c55e', '#ef4444', '#f59e0b', '#6366f1'];

function StatCard({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: number | string; color: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4 shadow-sm">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon className="h-5 w-5 text-white" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trends, setTrends] = useState<EmailTrendPoint[]>([]);
  const [accounts, setAccounts] = useState<AccountPerformance[]>([]);
  const [recentJobs, setRecentJobs] = useState<EmailJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  const load = async () => {
    try {
      const [s, t, a, h] = await Promise.all([
        dashboardApi.summary(),
        dashboardApi.emailTrends(days),
        dashboardApi.accountPerformance(),
        historyApi.list({ per_page: 5 }),
      ]);
      setSummary(s.data);
      setTrends(t.data.trends);
      setAccounts(a.data.accounts);
      setRecentJobs(h.data.items);
    } catch {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [days]);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>
  );

  const statusDist = summary ? [
    { name: 'Accepted', value: summary.accepted_emails },
    { name: 'Failed', value: summary.failed_emails },
    { name: 'Pending', value: summary.pending_emails + summary.retrying_emails },
    { name: 'Cancelled', value: summary.cancelled_emails },
  ] : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">Your email platform overview</p>
        </div>
        <div className="flex gap-2">
          {[7, 30, 90].map(d => (
            <button key={d} onClick={() => setDays(d)}
              className={cn('px-3 py-1.5 text-sm rounded-lg border transition-colors', days === d ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-200 text-gray-600 hover:bg-gray-50')}>
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard icon={Mail} label="Total Emails" value={summary?.total_emails ?? 0} color="bg-blue-500" />
        <StatCard icon={CheckCircle} label="Accepted" value={summary?.accepted_emails ?? 0} color="bg-green-500" />
        <StatCard icon={XCircle} label="Failed" value={summary?.failed_emails ?? 0} color="bg-red-500" />
        <StatCard icon={Clock} label="Pending" value={summary?.pending_emails ?? 0} color="bg-yellow-500" />
        <StatCard icon={RefreshCw} label="Retrying" value={summary?.retrying_emails ?? 0} color="bg-orange-500" />
        <StatCard icon={Server} label="Active SMTP" value={summary?.active_smtp_accounts ?? 0} color="bg-indigo-500" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Email Activity Line Chart */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-blue-600" /> Email Activity ({days}d)
          </h2>
          {trends.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">No data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="submitted" stroke="#6366f1" name="Submitted" dot={false} />
                <Line type="monotone" dataKey="accepted" stroke="#22c55e" name="Accepted" dot={false} />
                <Line type="monotone" dataKey="failed" stroke="#ef4444" name="Failed" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Status Distribution Pie */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Status Distribution</h2>
          {statusDist.every(d => d.value === 0) ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">No emails yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={statusDist} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false} style={{ fontSize: 10 }}>
                  {statusDist.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Account Performance */}
      {accounts.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900 mb-4">SMTP Account Performance</h2>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={accounts}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="account_name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="accepted" fill="#22c55e" name="Accepted" radius={[4, 4, 0, 0]} />
              <Bar dataKey="failed" fill="#ef4444" name="Failed" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent Activity */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Recent Email Activity</h2>
          <Link to="/history" className="text-sm text-blue-600 hover:text-blue-700">View all →</Link>
        </div>
        {recentJobs.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">No emails sent yet. <Link to="/compose" className="text-blue-600">Compose your first email →</Link></div>
        ) : (
          <div className="divide-y divide-gray-50">
            {recentJobs.map(job => (
              <div key={job.id} className="px-5 py-3 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{job.subject}</p>
                  <p className="text-xs text-gray-500">{job.recipient_count} recipient(s) · {formatRelative(job.created_at)}</p>
                </div>
                <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', statusColor(job.status))}>
                  {job.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
