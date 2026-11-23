import { useEffect, useState, useRef } from 'react';
import { contactsApi } from '../api/contacts';
import type { Contact, PaginatedResponse } from '../types';
import { formatDate } from '../utils';
import { toast } from 'sonner';
import { getErrorMessage } from '../utils';
import { Plus, Search, Upload, Download, Edit, Trash2, X, Loader2, Users } from 'lucide-react';

function ContactModal({ contact, onClose, onSave }: {
  contact: Contact | null;
  onClose: () => void;
  onSave: (data: Partial<Contact>) => Promise<void>;
}) {
  const [form, setForm] = useState({
    name: contact?.name || '',
    email: contact?.email || '',
    organization: contact?.organization || '',
    group_name: contact?.group_name || '',
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.email) { toast.error('Name and email required'); return; }
    setSaving(true);
    try { await onSave(form); }
    finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-md shadow-xl">
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">{contact ? 'Edit Contact' : 'Add Contact'}</h3>
          <button onClick={onClose}><X className="h-5 w-5 text-gray-500" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-3">
          {[
            { k: 'name', label: 'Name *', placeholder: 'John Doe' },
            { k: 'email', label: 'Email *', placeholder: 'john@example.com' },
            { k: 'organization', label: 'Organization', placeholder: 'Acme Corp' },
            { k: 'group_name', label: 'Group', placeholder: 'Newsletter' },
          ].map(({ k, label, placeholder }) => (
            <div key={k}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
              <input value={(form as Record<string, string>)[k]}
                onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
                placeholder={placeholder} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            </div>
          ))}
          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={saving}
              className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-60 flex items-center justify-center gap-2">
              {saving && <Loader2 className="h-4 w-4 animate-spin" />} Save
            </button>
            <button type="button" onClick={onClose} className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function ContactsPage() {
  const [data, setData] = useState<PaginatedResponse<Contact>>({ items: [], total: 0, page: 1, per_page: 20, pages: 0 });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [group, setGroup] = useState('');
  const [page, setPage] = useState(1);
  const [editContact, setEditContact] = useState<Contact | null | 'new'>('new');
  const [showModal, setShowModal] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = async (pg = page, q = search, g = group) => {
    try {
      const { data: res } = await contactsApi.list({ page: pg, per_page: 20, search: q || undefined, group: g || undefined });
      setData(res);
    } catch { toast.error('Failed to load contacts'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [page, search, group]);

  const handleSave = async (formData: Partial<Contact>) => {
    try {
      if (editContact && editContact !== 'new') {
        const { data: updated } = await contactsApi.update(editContact.id, formData);
        setData(d => ({ ...d, items: d.items.map(c => c.id === updated.id ? updated : c) }));
        toast.success('Contact updated');
      } else {
        const { data: created } = await contactsApi.create(formData);
        toast.success('Contact added');
        await load();
      }
      setShowModal(false);
    } catch (err) { toast.error(getErrorMessage(err)); throw err; }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this contact?')) return;
    try { await contactsApi.delete(id); setData(d => ({ ...d, items: d.items.filter(c => c.id !== id), total: d.total - 1 })); toast.success('Deleted'); }
    catch { toast.error('Failed to delete'); }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const { data: res } = await contactsApi.import(file);
      toast.success(`Imported ${res.imported}, skipped ${res.skipped}`);
      await load();
    } catch { toast.error('Import failed'); }
    e.target.value = '';
  };

  const handleExport = async () => {
    try {
      const { data: blob } = await contactsApi.export();
      const url = URL.createObjectURL(blob as Blob);
      const a = document.createElement('a'); a.href = url; a.download = 'contacts.csv'; a.click();
      URL.revokeObjectURL(url);
    } catch { toast.error('Export failed'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Contacts</h1>
          <p className="text-gray-500 text-sm mt-1">{data.total} contact{data.total !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => fileRef.current?.click()} className="flex items-center gap-1.5 border border-gray-300 px-3 py-2 rounded-lg text-sm hover:bg-gray-50">
            <Upload className="h-4 w-4" /> Import CSV
          </button>
          <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={handleImport} />
          <button onClick={handleExport} className="flex items-center gap-1.5 border border-gray-300 px-3 py-2 rounded-lg text-sm hover:bg-gray-50">
            <Download className="h-4 w-4" /> Export
          </button>
          <button onClick={() => { setEditContact('new'); setShowModal(true); }}
            className="flex items-center gap-1.5 bg-blue-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-blue-700">
            <Plus className="h-4 w-4" /> Add Contact
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search contacts..." className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
        <input value={group} onChange={e => { setGroup(e.target.value); setPage(1); }}
          placeholder="Filter by group..." className="w-40 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
      </div>

      {data.items.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-16 text-center">
          <Users className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-sm">No contacts found. Add your first contact or import from CSV.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                {['Name', 'Email', 'Organization', 'Group', 'Added', 'Actions'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {data.items.map(c => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{c.name}</td>
                  <td className="px-4 py-3 text-gray-600">{c.email}</td>
                  <td className="px-4 py-3 text-gray-500">{c.organization || '—'}</td>
                  <td className="px-4 py-3">{c.group_name ? <span className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full">{c.group_name}</span> : '—'}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(c.created_at)}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      <button onClick={() => { setEditContact(c); setShowModal(true); }} className="p-1.5 text-gray-600 hover:bg-gray-100 rounded"><Edit className="h-3.5 w-3.5" /></button>
                      <button onClick={() => handleDelete(c.id)} className="p-1.5 text-red-600 hover:bg-red-50 rounded"><Trash2 className="h-3.5 w-3.5" /></button>
                    </div>
                  </td>
                </tr>
              ))}
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

      {showModal && (
        <ContactModal
          contact={editContact !== 'new' ? editContact : null}
          onClose={() => setShowModal(false)}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
