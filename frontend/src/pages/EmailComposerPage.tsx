import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { smtpAccountsApi } from '../api/smtpAccounts';
import { templatesApi } from '../api/templates';
import { emailsApi } from '../api/emails';
import { contactsApi } from '../api/contacts';
import type { SMTPAccount, EmailTemplate, Contact, RecipientItem } from '../types';
import { toast } from 'sonner';
import { getErrorMessage, cn } from '../utils';
import {
  Send, Paperclip, X, Plus, FileText, Users, Loader2, Eye, ChevronDown,
} from 'lucide-react';

export default function EmailComposerPage() {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<SMTPAccount[]>([]);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);

  const [form, setForm] = useState({
    smtp_account_id: '',
    subject: '',
    html_body: '',
    text_body: '',
    reply_to: '',
    template_id: '',
    template_variables: {} as Record<string, string>,
  });

  const [recipients, setRecipients] = useState<RecipientItem[]>([]);
  const [recipientInput, setRecipientInput] = useState('');
  const [recipientType, setRecipientType] = useState<'to' | 'cc' | 'bcc'>('to');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [sending, setSending] = useState(false);
  const [showContactPicker, setShowContactPicker] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [bodyMode, setBodyMode] = useState<'html' | 'text'>('html');
  const [loading, setLoading] = useState(true);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    Promise.all([
      smtpAccountsApi.list(),
      templatesApi.list(),
      contactsApi.list({ per_page: 100 }),
    ]).then(([a, t, c]) => {
      setAccounts(a.data);
      setTemplates(t.data);
      setContacts(c.data.items);
      const def = a.data.find(acc => acc.is_default) || a.data[0];
      if (def) setForm(f => ({ ...f, smtp_account_id: def.id }));
    }).catch(() => toast.error('Failed to load resources')).finally(() => setLoading(false));
  }, []);

  const addRecipient = (email: string, name?: string, type: 'to' | 'cc' | 'bcc' = recipientType) => {
    if (!email || !/\S+@\S+\.\S+/.test(email)) { toast.error('Invalid email address'); return; }
    if (recipients.some(r => r.email === email)) { toast.error('Recipient already added'); return; }
    setRecipients(r => [...r, { email, name, type }]);
  };

  const handleAddRecipientInput = () => {
    if (recipientInput.trim()) {
      addRecipient(recipientInput.trim());
      setRecipientInput('');
    }
  };

  const handleTemplateSelect = async (templateId: string) => {
    setForm(f => ({ ...f, template_id: templateId }));
    if (!templateId) return;
    const tmpl = templates.find(t => t.id === templateId);
    if (tmpl) {
      setForm(f => ({
        ...f,
        subject: tmpl.subject,
        html_body: tmpl.html_content || '',
        text_body: tmpl.text_content || '',
      }));
    }
  };

  const handleSend = async () => {
    if (!form.smtp_account_id) { toast.error('Select an SMTP account'); return; }
    if (!form.subject.trim()) { toast.error('Subject is required'); return; }
    if (!recipients.some(r => r.type === 'to')) { toast.error('At least one To recipient required'); return; }
    if (!form.html_body && !form.text_body) { toast.error('Email body cannot be empty'); return; }

    setSending(true);
    try {
      const fd = new FormData();
      fd.append('smtp_account_id', form.smtp_account_id);
      fd.append('subject', form.subject);
      fd.append('recipients_json', JSON.stringify(recipients));
      if (form.html_body) fd.append('html_body', form.html_body);
      if (form.text_body) fd.append('text_body', form.text_body);
      if (form.reply_to) fd.append('reply_to', form.reply_to);
      if (form.template_id) fd.append('template_id', form.template_id);
      if (Object.keys(form.template_variables).length > 0)
        fd.append('template_variables_json', JSON.stringify(form.template_variables));
      attachments.forEach(file => fd.append('attachments', file));

      const { data } = await emailsApi.send(fd);
      toast.success(`Email queued! Job ID: ${data.id.slice(0, 8)}...`);
      navigate(`/history/${data.id}`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSending(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compose Email</h1>
        <p className="text-gray-500 text-sm mt-1">Create and send an email via your configured SMTP accounts</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-6 space-y-4">
          {/* SMTP Account */}
          <div className="flex items-center gap-3 pb-3 border-b border-gray-100">
            <label className="text-sm font-medium text-gray-700 w-16 flex-shrink-0">From</label>
            <select value={form.smtp_account_id} onChange={e => setForm(f => ({ ...f, smtp_account_id: e.target.value }))}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent">
              <option value="">Select SMTP account...</option>
              {accounts.filter(a => a.is_active).map(a => (
                <option key={a.id} value={a.id}>{a.sender_name || a.sender_email} ({a.account_name})</option>
              ))}
            </select>
          </div>

          {/* Recipients */}
          <div className="pb-3 border-b border-gray-100">
            <div className="flex items-start gap-3 mb-2">
              <label className="text-sm font-medium text-gray-700 w-16 flex-shrink-0 pt-2">To</label>
              <div className="flex-1">
                <div className="flex flex-wrap gap-1 mb-2">
                  {recipients.filter(r => r.type === 'to').map((r, i) => (
                    <span key={i} className="flex items-center gap-1 bg-blue-50 text-blue-800 text-xs px-2 py-1 rounded-full">
                      {r.name ? `${r.name} <${r.email}>` : r.email}
                      <button onClick={() => setRecipients(rs => rs.filter((_, j) => j !== recipients.indexOf(r)))}>
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <select value={recipientType} onChange={e => setRecipientType(e.target.value as 'to' | 'cc' | 'bcc')}
                    className="border border-gray-300 rounded px-2 py-1.5 text-xs">
                    <option value="to">To</option>
                    <option value="cc">CC</option>
                    <option value="bcc">BCC</option>
                  </select>
                  <input value={recipientInput} onChange={e => setRecipientInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), handleAddRecipientInput())}
                    placeholder="Add email address..." className="flex-1 border border-gray-300 rounded px-3 py-1.5 text-sm" />
                  <button onClick={handleAddRecipientInput} className="bg-gray-100 hover:bg-gray-200 px-3 py-1.5 rounded text-sm transition-colors"><Plus className="h-4 w-4" /></button>
                  <button onClick={() => setShowContactPicker(true)} className="border border-gray-300 px-3 py-1.5 rounded text-sm flex items-center gap-1 hover:bg-gray-50">
                    <Users className="h-3.5 w-3.5" /> Contacts
                  </button>
                </div>
              </div>
            </div>
            {/* CC/BCC tags */}
            {recipients.filter(r => r.type !== 'to').map((r, i) => (
              <div key={i} className="flex items-center gap-2 mt-1 ml-16">
                <span className="text-xs text-gray-500 uppercase font-medium">{r.type}</span>
                <span className="flex items-center gap-1 bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded-full">
                  {r.email}
                  <button onClick={() => setRecipients(rs => rs.filter((_, j) => rs.indexOf(r) !== j))}><X className="h-3 w-3" /></button>
                </span>
              </div>
            ))}
          </div>

          {/* Subject */}
          <div className="flex items-center gap-3 pb-3 border-b border-gray-100">
            <label className="text-sm font-medium text-gray-700 w-16 flex-shrink-0">Subject</label>
            <input value={form.subject} onChange={e => setForm(f => ({ ...f, subject: e.target.value }))}
              placeholder="Email subject..." className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
          </div>

          {/* Template Picker */}
          <div className="flex items-center gap-3 pb-3 border-b border-gray-100">
            <label className="text-sm font-medium text-gray-700 w-16 flex-shrink-0 flex items-center gap-1"><FileText className="h-3.5 w-3.5" />Template</label>
            <select value={form.template_id} onChange={e => handleTemplateSelect(e.target.value)}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm">
              <option value="">No template (compose freely)</option>
              {templates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>

          {/* Body */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-medium text-gray-700">Body</span>
              <div className="flex border border-gray-200 rounded overflow-hidden text-xs">
                <button onClick={() => setBodyMode('html')} className={cn('px-3 py-1', bodyMode === 'html' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50')}>HTML</button>
                <button onClick={() => setBodyMode('text')} className={cn('px-3 py-1', bodyMode === 'text' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50')}>Plain Text</button>
              </div>
              <button onClick={() => setShowPreview(true)} className="ml-auto flex items-center gap-1 text-xs text-gray-500 hover:text-gray-900">
                <Eye className="h-3.5 w-3.5" /> Preview
              </button>
            </div>
            {bodyMode === 'html' ? (
              <textarea value={form.html_body} onChange={e => setForm(f => ({ ...f, html_body: e.target.value }))}
                rows={12} placeholder="<h1>Hello!</h1><p>Your message here...</p>"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y" />
            ) : (
              <textarea value={form.text_body} onChange={e => setForm(f => ({ ...f, text_body: e.target.value }))}
                rows={12} placeholder="Your plain text message here..."
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y" />
            )}
          </div>

          {/* Reply-To */}
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700 w-16 flex-shrink-0">Reply-To</label>
            <input value={form.reply_to} onChange={e => setForm(f => ({ ...f, reply_to: e.target.value }))}
              placeholder="optional@example.com" className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>

          {/* Attachments */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-medium text-gray-700">Attachments</span>
              <button onClick={() => fileRef.current?.click()} className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800">
                <Paperclip className="h-3.5 w-3.5" /> Add file
              </button>
              <input ref={fileRef} type="file" multiple className="hidden"
                onChange={e => setAttachments(a => [...a, ...Array.from(e.target.files || [])])} />
            </div>
            {attachments.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {attachments.map((f, i) => (
                  <div key={i} className="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded text-xs text-gray-700">
                    <Paperclip className="h-3 w-3" />{f.name}
                    <button onClick={() => setAttachments(a => a.filter((_, j) => j !== i))}><X className="h-3 w-3 text-gray-500 hover:text-red-600" /></button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50 rounded-b-xl">
          <p className="text-xs text-gray-400">Email will be queued and processed by the background worker</p>
          <button onClick={handleSend} disabled={sending}
            className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-60 transition-colors">
            {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            {sending ? 'Sending...' : 'Send Email'}
          </button>
        </div>
      </div>

      {/* Contact Picker Modal */}
      {showContactPicker && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md shadow-xl">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Select Contact</h3>
              <button onClick={() => setShowContactPicker(false)}><X className="h-5 w-5 text-gray-500" /></button>
            </div>
            <div className="p-4 max-h-80 overflow-y-auto space-y-1">
              {contacts.map(c => (
                <button key={c.id} onClick={() => { addRecipient(c.email, c.name); setShowContactPicker(false); }}
                  className="w-full text-left px-3 py-2 hover:bg-blue-50 rounded-lg flex items-center gap-3 text-sm">
                  <div className="bg-blue-100 text-blue-700 rounded-full w-7 h-7 flex items-center justify-center text-xs font-medium flex-shrink-0">
                    {c.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{c.name}</p>
                    <p className="text-xs text-gray-500">{c.email}</p>
                  </div>
                </button>
              ))}
              {contacts.length === 0 && <p className="text-center text-gray-400 py-4 text-sm">No contacts yet</p>}
            </div>
          </div>
        </div>
      )}

      {/* HTML Preview Modal */}
      {showPreview && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl shadow-xl max-h-[80vh] flex flex-col">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Email Preview</h3>
              <button onClick={() => setShowPreview(false)}><X className="h-5 w-5 text-gray-500" /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <div className="mb-3 pb-3 border-b border-gray-100 text-sm space-y-1 text-gray-600">
                <p><span className="font-medium">Subject:</span> {form.subject || '(empty)'}</p>
              </div>
              {form.html_body ? (
                <iframe srcDoc={form.html_body} className="w-full h-96 border-0" title="Email Preview" />
              ) : (
                <pre className="whitespace-pre-wrap text-sm text-gray-700">{form.text_body || '(empty)'}</pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
