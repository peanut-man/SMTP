import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, FileText, Edit, Trash2, Copy, Eye, X } from 'lucide-react';
import { templatesApi } from '../api/templates';
import type { EmailTemplate } from '../types';
import { formatDate } from '../utils';
import { toast } from 'sonner';

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewTemplate, setPreviewTemplate] = useState<EmailTemplate | null>(null);
  const navigate = useNavigate();

  const load = async () => {
    try {
      const { data } = await templatesApi.list();
      setTemplates(data);
    } catch { toast.error('Failed to load templates'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete template "${name}"?`)) return;
    try {
      await templatesApi.delete(id);
      toast.success('Template deleted');
      setTemplates(ts => ts.filter(t => t.id !== id));
    } catch { toast.error('Failed to delete template'); }
  };

  const handleDuplicate = async (tmpl: EmailTemplate) => {
    try {
      const { data } = await templatesApi.create({
        name: `${tmpl.name} (Copy)`,
        description: tmpl.description || undefined,
        subject: tmpl.subject,
        html_content: tmpl.html_content || undefined,
        text_content: tmpl.text_content || undefined,
        variables: tmpl.variables || undefined,
      });
      toast.success('Template duplicated');
      setTemplates(ts => [data, ...ts]);
    } catch { toast.error('Failed to duplicate template'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Email Templates</h1>
          <p className="text-gray-500 text-sm mt-1">Create reusable email templates with dynamic variables</p>
        </div>
        <Link to="/templates/new" className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          <Plus className="h-4 w-4" /> New Template
        </Link>
      </div>

      {templates.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-16 text-center">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">No templates yet</h2>
          <p className="text-gray-500 text-sm mb-6">Create reusable templates with Jinja2 variables.</p>
          <Link to="/templates/new" className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">Create Template</Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map(tmpl => (
            <div key={tmpl.id} className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="p-5">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-900 truncate">{tmpl.name}</h3>
                </div>
                {tmpl.description && <p className="text-sm text-gray-500 mb-2 line-clamp-2">{tmpl.description}</p>}
                <p className="text-xs text-gray-400 mb-3">Subject: {tmpl.subject}</p>
                {tmpl.variables && tmpl.variables.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {tmpl.variables.map(v => (
                      <span key={v} className="text-xs bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full font-mono">{'{{' + v + '}}'}</span>
                    ))}
                  </div>
                )}
                <p className="text-xs text-gray-400">Updated {formatDate(tmpl.updated_at)}</p>
              </div>
              <div className="px-5 py-3 border-t border-gray-100 flex items-center gap-1">
                <button onClick={() => setPreviewTemplate(tmpl)} className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900 px-2 py-1 hover:bg-gray-100 rounded">
                  <Eye className="h-3.5 w-3.5" /> Preview
                </button>
                <button onClick={() => navigate(`/templates/${tmpl.id}/edit`)} className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900 px-2 py-1 hover:bg-gray-100 rounded">
                  <Edit className="h-3.5 w-3.5" /> Edit
                </button>
                <button onClick={() => handleDuplicate(tmpl)} className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900 px-2 py-1 hover:bg-gray-100 rounded">
                  <Copy className="h-3.5 w-3.5" /> Copy
                </button>
                <button onClick={() => handleDelete(tmpl.id, tmpl.name)} className="flex items-center gap-1 text-xs text-red-600 hover:text-red-800 px-2 py-1 hover:bg-red-50 rounded ml-auto">
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {previewTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl shadow-xl max-h-[80vh] flex flex-col">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">{previewTemplate.name}</h3>
              <button onClick={() => setPreviewTemplate(null)}><X className="h-5 w-5 text-gray-500" /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <p className="text-sm text-gray-500 mb-3">Subject: {previewTemplate.subject}</p>
              {previewTemplate.html_content ? (
                <iframe srcDoc={previewTemplate.html_content} className="w-full h-80 border border-gray-200 rounded" title="Template Preview" />
              ) : (
                <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded">{previewTemplate.text_content}</pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
