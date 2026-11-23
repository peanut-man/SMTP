import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { templatesApi } from '../api/templates';
import { toast } from 'sonner';
import { getErrorMessage } from '../utils';
import { ArrowLeft, Save, Loader2, Eye, X } from 'lucide-react';

export default function TemplateEditorPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [form, setForm] = useState({
    name: '', description: '', subject: '', html_content: '', text_content: '',
  });
  const [loading, setLoading] = useState(false);
  const [fetchLoading, setFetchLoading] = useState(isEdit);
  const [previewVars, setPreviewVars] = useState<Record<string, string>>({});
  const [showPreview, setShowPreview] = useState(false);
  const [previewResult, setPreviewResult] = useState<{ subject: string; html_content?: string; text_content?: string } | null>(null);

  useEffect(() => {
    if (isEdit && id) {
      templatesApi.get(id).then(({ data }) => {
        setForm({ name: data.name, description: data.description || '', subject: data.subject, html_content: data.html_content || '', text_content: data.text_content || '' });
        if (data.variables) {
          const vars: Record<string, string> = {};
          data.variables.forEach(v => { vars[v] = `[${v}]`; });
          setPreviewVars(vars);
        }
      }).catch(() => toast.error('Failed to load template')).finally(() => setFetchLoading(false));
    }
  }, [id, isEdit]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name) { toast.error('Template name is required'); return; }
    if (!form.subject) { toast.error('Subject is required'); return; }
    setLoading(true);
    try {
      if (isEdit && id) {
        await templatesApi.update(id, form);
        toast.success('Template updated');
      } else {
        await templatesApi.create(form);
        toast.success('Template created');
      }
      navigate('/templates');
    } catch (err) { toast.error(getErrorMessage(err)); }
    finally { setLoading(false); }
  };

  const handlePreview = async () => {
    if (!id) { toast.error('Save first to preview'); return; }
    try {
      const { data } = await templatesApi.preview(id, previewVars);
      setPreviewResult(data as { subject: string; html_content?: string; text_content?: string });
      setShowPreview(true);
    } catch { toast.error('Preview failed'); }
  };

  if (fetchLoading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  return (
    <div className="max-w-3xl">
      <button onClick={() => navigate('/templates')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 mb-6">
        <ArrowLeft className="h-4 w-4" /> Back to Templates
      </button>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-xl font-bold text-gray-900">{isEdit ? 'Edit Template' : 'New Template'}</h1>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Template Name *</label>
              <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                placeholder="Welcome Email" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject *</label>
              <input value={form.subject} onChange={e => setForm(f => ({ ...f, subject: e.target.value }))}
                placeholder="Welcome {{ name }}!" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              placeholder="Sent to new users on registration" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">HTML Content</label>
            <p className="text-xs text-gray-400 mb-1">Use <code className="bg-gray-100 px-1 rounded">{`{{ variable_name }}`}</code> for dynamic content</p>
            <textarea value={form.html_content} onChange={e => setForm(f => ({ ...f, html_content: e.target.value }))}
              rows={10} placeholder="<h1>Hello {{ name }}!</h1>"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono resize-y focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Plain Text Content</label>
            <textarea value={form.text_content} onChange={e => setForm(f => ({ ...f, text_content: e.target.value }))}
              rows={5} placeholder="Hello {{ name }}!"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono resize-y" />
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button type="submit" disabled={loading}
              className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-60">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              {isEdit ? 'Save Changes' : 'Create Template'}
            </button>
            {isEdit && (
              <button type="button" onClick={handlePreview} className="flex items-center gap-2 border border-gray-300 px-4 py-2 rounded-lg text-sm hover:bg-gray-50">
                <Eye className="h-4 w-4" /> Preview
              </button>
            )}
            <button type="button" onClick={() => navigate('/templates')} className="text-sm text-gray-500 hover:text-gray-900">Cancel</button>
          </div>
        </form>
      </div>

      {showPreview && previewResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl shadow-xl max-h-[80vh] flex flex-col">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="font-semibold">Preview: {previewResult.subject}</h3>
              <button onClick={() => setShowPreview(false)}><X className="h-5 w-5 text-gray-500" /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {previewResult.html_content
                ? <iframe srcDoc={previewResult.html_content} className="w-full h-80 border-0" title="Preview" />
                : <pre className="whitespace-pre-wrap text-sm text-gray-700">{previewResult.text_content}</pre>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
