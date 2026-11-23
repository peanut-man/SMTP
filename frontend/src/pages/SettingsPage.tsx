import { useAuth } from '../hooks/useAuth';
import { formatDate } from '../utils';
import { User, Shield, Settings } from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 text-sm mt-1">Manage your account preferences</p>
      </div>

      {/* Profile */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100 flex items-center gap-2">
          <User className="h-5 w-5 text-gray-500" />
          <h2 className="font-semibold text-gray-900">Profile</h2>
        </div>
        <div className="p-5 space-y-4 text-sm">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Username</label>
              <p className="font-medium text-gray-900">{user?.username}</p>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Email</label>
              <p className="font-medium text-gray-900">{user?.email}</p>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Role</label>
              <span className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs font-medium capitalize">{user?.role}</span>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Account Status</label>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${user?.is_active ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                {user?.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Security */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100 flex items-center gap-2">
          <Shield className="h-5 w-5 text-gray-500" />
          <h2 className="font-semibold text-gray-900">Security</h2>
        </div>
        <div className="p-5 text-sm space-y-3">
          <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
            <div>
              <p className="font-medium text-blue-900">JWT Authentication</p>
              <p className="text-xs text-blue-700 mt-0.5">Your session is secured with a JWT token stored in your browser.</p>
            </div>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-medium">Active</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
            <div>
              <p className="font-medium text-green-900">SMTP Credential Encryption</p>
              <p className="text-xs text-green-700 mt-0.5">All SMTP passwords are encrypted with Fernet symmetric encryption.</p>
            </div>
            <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded font-medium">Enabled</span>
          </div>
        </div>
      </div>

      {/* App Info */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100 flex items-center gap-2">
          <Settings className="h-5 w-5 text-gray-500" />
          <h2 className="font-semibold text-gray-900">Application</h2>
        </div>
        <div className="p-5 text-sm">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-xs text-gray-500 uppercase font-medium">Platform</label><p className="mt-1 font-medium">MailFlow SMTP Platform</p></div>
            <div><label className="text-xs text-gray-500 uppercase font-medium">Version</label><p className="mt-1 font-medium">1.0.0</p></div>
            <div><label className="text-xs text-gray-500 uppercase font-medium">Backend</label><p className="mt-1">FastAPI + Python 3.12</p></div>
            <div><label className="text-xs text-gray-500 uppercase font-medium">Database</label><p className="mt-1">PostgreSQL</p></div>
          </div>
        </div>
      </div>
    </div>
  );
}
