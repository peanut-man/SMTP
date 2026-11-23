import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { smtpAccountsApi } from '../api/smtpAccounts';
import type { SMTPTestResult } from '../types';
import { toast } from 'sonner';
import { getErrorMessage } from '../utils';
import { Loader2, Wifi, Save, ArrowLeft, CheckCircle, XCircle } from 'lucide-react';

const SECURITY_MODES = [
  { value: 'STARTTLS', label: 'STARTTLS (port 587 recommended)' },
  { value: 'SSL_TLS', label: 'SSL/TLS (port 465 recommended)' },
  { value: 'PLAIN', label: 'Plain SMTP (development only)' },
];

type TestResult = SMTPTestResult | { success: boolean; message: string; details?: string | null } | null;

export default function SMTPAccountFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [form, setForm] = useState<{
    account_name: string;
    smtp_host: string;
    smtp_port: string;
    username: string;
    password: string;
    security_mode: 'STARTTLS' | 'SSL_TLS' | 'PLAIN';
    sender_email: string;
    sender_name: string;
    connection_timeout: string;
    is_default: boolean;
  }>({
    account_name: '', smtp_host: '', smtp_port: '587', username: '', password: '',
    security_mode: 'STARTTLS', sender_email: '', sender_name: '', connection_timeout: '30',
    is_default: false,
  });
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [fetchLoading, setFetchLoading] = useState(isEdit);
  const [testResult, setTestResult] = useState<TestResult>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isEdit && id) {
      smtpAccountsApi.get(id).then(({ data }) => {
        setForm({
          account_name: data.account_name, smtp_host: data.smtp_host,
          smtp_port: String(data.smtp_port), username: data.username, password: '',
          security_mode: data.security_mode, sender_email: data.sender_email,
          sender_name: data.sender_name, connection_timeout: String(data.connection_timeout),
          is_default: data.is_default,
        });
      }).catch(() => toast.error('Failed to load account')).finally(() => setFetchLoading(false));
    }
  }, [id, isEdit]);

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!form.account_name) errs.account_name = 'Required';
    if (!form.smtp_host) errs.smtp_host = 'Required';
    if (!form.smtp_port || isNaN(Number(form.smtp_port))) errs.smtp_port = 'Valid port required';
    if (!form.username) errs.username = 'Required';
    if (!isEdit && !form.password) errs.password = 'Required';
    if (!form.sender_email || !/\S+@\S+\.\S+/.test(form.sender_email)) errs.sender_email = 'Valid email required';
    return errs;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) { setErrors(errs); return; }
    setLoading(true);
    try {
      const payload = { ...form, smtp_port: Number(form.smtp_port), connection_timeout: Number(form.connection_timeout) };
      if (isEdit && id) {
        if (!payload.password) delete (payload as Record<string, unknown>).password;
        await smtpAccountsApi.update(id, payload);
        toast.success('SMTP account updated');
      } else {
        await smtpAccountsApi.create(payload as typeof payload & { password: string });
        toast.success('SMTP account created');
      }
      navigate('/smtp-accounts');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    if (!id) { toast.error('Save the account first to test it'); return; }
    setTesting(true);
    setTestResult(null);
    try {
      const { data } = await smtpAccountsApi.test(id);
      setTestResult(data);
    } catch (err) {
      setTestResult({ success: false, message: getErrorMessage(err) });
    } finally {
      setTesting(false);
    }
  };

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [k]: e.target.type === 'checkbox' ? (e.target as HTMLInputElement).checked : (e.target.value as any) }));

  if (fetchLoading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  return (
    <div className="max-w-2xl">
      <button onClick={() => navigate('/smtp-accounts')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 mb-6">
        <ArrowLeft className="h-4 w-4" /> Back to Accounts
      </button>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-xl font-bold text-gray-900">{isEdit ? 'Edit SMTP Account' : 'Add SMTP Account'}</h1>
          <p className="text-gray-500 text-sm mt-1">Configure your SMTP server connection</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Account Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Account Name *</label>
            <input value={form.account_name} onChange={set('account_name')} placeholder="e.g. Gmail Production"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            {errors.account_name && <p className="mt-1 text-xs text-red-600">{errors.account_name}</p>}
          </div>

          {/* Host + Port */}
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">SMTP Host *</label>
              <input value={form.smtp_host} onChange={set('smtp_host')} placeholder="smtp.gmail.com"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              {errors.smtp_host && <p className="mt-1 text-xs text-red-600">{errors.smtp_host}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Port *</label>
              <input value={form.smtp_port} onChange={set('smtp_port')} placeholder="587" type="number"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              {errors.smtp_port && <p className="mt-1 text-xs text-red-600">{errors.smtp_port}</p>}
            </div>
          </div>

          {/* Security Mode */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Security Mode</label>
            <select value={form.security_mode} onChange={set('security_mode')}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent">
              {SECURITY_MODES.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </div>

          {/* Credentials */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Username *</label>
              <input value={form.username} onChange={set('username')} placeholder="your@email.com"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              {errors.username && <p className="mt-1 text-xs text-red-600">{errors.username}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password {isEdit && <span className="text-gray-400 font-normal">(leave blank to keep)</span>}</label>
              <input type="password" value={form.password} onChange={set('password')} placeholder="••••••••"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password}</p>}
            </div>
          </div>

          {/* Sender */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Sender Email *</label>
              <input value={form.sender_email} onChange={set('sender_email')} placeholder="noreply@example.com"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              {errors.sender_email && <p className="mt-1 text-xs text-red-600">{errors.sender_email}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Sender Name</label>
              <input value={form.sender_name} onChange={set('sender_name')} placeholder="My App"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            </div>
          </div>

          {/* Options */}
          <div className="flex items-center gap-3">
            <input type="checkbox" id="is_default" checked={form.is_default} onChange={set('is_default')}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
            <label htmlFor="is_default" className="text-sm text-gray-700">Set as default account</label>
          </div>

          {/* Test Result */}
          {testResult && (
            <div className={`flex items-start gap-2 p-3 rounded-lg text-sm ${testResult.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
              {testResult.success ? <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0" /> : <XCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />}
              <div>
                <p className="font-medium">{testResult.message}</p>
                {testResult.details && <p className="text-xs mt-0.5 opacity-80">{testResult.details}</p>}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-3 pt-2">
            <button type="submit" disabled={loading}
              className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-60">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              {isEdit ? 'Save Changes' : 'Create Account'}
            </button>
            {isEdit && (
              <button type="button" onClick={handleTest} disabled={testing}
                className="flex items-center gap-2 border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-60">
                {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wifi className="h-4 w-4" />}
                Test Connection
              </button>
            )}
            <button type="button" onClick={() => navigate('/smtp-accounts')}
              className="text-sm text-gray-500 hover:text-gray-900 px-3 py-2">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}
