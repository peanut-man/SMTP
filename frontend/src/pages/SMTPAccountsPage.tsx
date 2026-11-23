import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Server, CheckCircle2, XCircle, Wifi, Star, Trash2, Edit, ToggleLeft, ToggleRight, Loader2 } from 'lucide-react';
import { smtpAccountsApi } from '../api/smtpAccounts';
import type { SMTPAccount } from '../types';
import { formatDate, cn } from '../utils';
import { toast } from 'sonner';

function TestBadge({ status }: { status: string }) {
  if (status === 'success') return <span className="flex items-center gap-1 text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded-full"><CheckCircle2 className="h-3 w-3" />Passed</span>;
  if (status === 'failed') return <span className="flex items-center gap-1 text-xs text-red-700 bg-red-50 px-2 py-0.5 rounded-full"><XCircle className="h-3 w-3" />Failed</span>;
  return <span className="text-xs text-gray-400">Not tested</span>;
}

export default function SMTPAccountsPage() {
  const [accounts, setAccounts] = useState<SMTPAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingId, setTestingId] = useState<string | null>(null);
  const navigate = useNavigate();

  const load = async () => {
    try {
      const { data } = await smtpAccountsApi.list();
      setAccounts(data);
    } catch {
      toast.error('Failed to load SMTP accounts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleTest = async (id: string) => {
    setTestingId(id);
    try {
      const { data } = await smtpAccountsApi.test(id);
      if (data.success) toast.success(data.message);
      else toast.error(data.message + (data.details ? ` (${data.details})` : ''));
      await load();
    } catch {
      toast.error('Connection test failed');
    } finally {
      setTestingId(null);
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await smtpAccountsApi.setDefault(id);
      toast.success('Default account updated');
      await load();
    } catch { toast.error('Failed to set default'); }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete SMTP account "${name}"? This cannot be undone.`)) return;
    try {
      await smtpAccountsApi.delete(id);
      toast.success('Account deleted');
      setAccounts(acc => acc.filter(a => a.id !== id));
    } catch { toast.error('Failed to delete account'); }
  };

  const handleToggle = async (account: SMTPAccount) => {
    try {
      await smtpAccountsApi.update(account.id, { is_active: !account.is_active });
      toast.success(account.is_active ? 'Account disabled' : 'Account enabled');
      await load();
    } catch { toast.error('Failed to update account'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">SMTP Accounts</h1>
          <p className="text-gray-500 text-sm mt-1">Manage your SMTP server configurations</p>
        </div>
        <Link to="/smtp-accounts/new" className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
          <Plus className="h-4 w-4" /> Add Account
        </Link>
      </div>

      {accounts.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-16 text-center">
          <Server className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">No SMTP accounts yet</h2>
          <p className="text-gray-500 text-sm mb-6">Add your first SMTP account to start sending emails.</p>
          <Link to="/smtp-accounts/new" className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">Add Account</Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                {['Account', 'Host / Port', 'Sender', 'Security', 'Status', 'Last Test', 'Actions'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {accounts.map(acc => (
                <tr key={acc.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{acc.account_name}</span>
                      {acc.is_default && <span className="flex items-center gap-0.5 text-xs text-yellow-700 bg-yellow-50 px-1.5 py-0.5 rounded-full"><Star className="h-2.5 w-2.5" fill="currentColor" />Default</span>}
                    </div>
                    <p className="text-xs text-gray-500">{acc.username}</p>
                  </td>
                  <td className="px-4 py-3 text-gray-700">{acc.smtp_host}:{acc.smtp_port}</td>
                  <td className="px-4 py-3">
                    <p className="text-gray-900">{acc.sender_name || '—'}</p>
                    <p className="text-xs text-gray-500">{acc.sender_email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn('px-2 py-0.5 rounded text-xs font-medium',
                      acc.security_mode === 'SSL_TLS' ? 'bg-green-50 text-green-700' :
                      acc.security_mode === 'STARTTLS' ? 'bg-blue-50 text-blue-700' : 'bg-gray-100 text-gray-600')}>
                      {acc.security_mode}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button onClick={() => handleToggle(acc)} className="flex items-center gap-1 text-xs">
                      {acc.is_active
                        ? <><ToggleRight className="h-4 w-4 text-green-600" /><span className="text-green-700">Active</span></>
                        : <><ToggleLeft className="h-4 w-4 text-gray-400" /><span className="text-gray-500">Inactive</span></>}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <TestBadge status={acc.last_test_status} />
                    {acc.last_tested_at && <p className="text-xs text-gray-400 mt-0.5">{formatDate(acc.last_tested_at)}</p>}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <button onClick={() => handleTest(acc.id)} disabled={testingId === acc.id}
                        className="p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors disabled:opacity-50" title="Test connection">
                        {testingId === acc.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Wifi className="h-3.5 w-3.5" />}
                      </button>
                      <button onClick={() => handleSetDefault(acc.id)} className="p-1.5 text-yellow-600 hover:bg-yellow-50 rounded transition-colors" title="Set as default">
                        <Star className="h-3.5 w-3.5" />
                      </button>
                      <button onClick={() => navigate(`/smtp-accounts/${acc.id}/edit`)} className="p-1.5 text-gray-600 hover:bg-gray-100 rounded transition-colors" title="Edit">
                        <Edit className="h-3.5 w-3.5" />
                      </button>
                      <button onClick={() => handleDelete(acc.id, acc.account_name)} className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors" title="Delete">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
