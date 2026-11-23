import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Server, Mail, FileText, Users, History, Settings,
} from 'lucide-react';
import { cn } from '../../utils';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/smtp-accounts', icon: Server, label: 'SMTP Accounts' },
  { to: '/compose', icon: Mail, label: 'Compose Email' },
  { to: '/templates', icon: FileText, label: 'Templates' },
  { to: '/contacts', icon: Users, label: 'Contacts' },
  { to: '/history', icon: History, label: 'Email History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="bg-blue-600 text-white p-1.5 rounded-lg">
            <Mail className="h-5 w-5" />
          </div>
          <span className="text-xl font-bold text-gray-900">MailFlow</span>
        </div>
        <p className="text-xs text-gray-500 mt-1">SMTP Management Platform</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )
            }
          >
            <Icon className="h-4 w-4 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
