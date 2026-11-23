import { Outlet } from 'react-router-dom';
import { Mail } from 'lucide-react';

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="bg-blue-600 text-white p-2 rounded-lg">
            <Mail className="h-6 w-6" />
          </div>
          <span className="text-2xl font-bold text-gray-900">MailFlow</span>
        </div>
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
