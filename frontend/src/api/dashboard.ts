import apiClient from './client';
import type { DashboardSummary, EmailTrendPoint, AccountPerformance } from '../types';

export const dashboardApi = {
  summary: () => apiClient.get<DashboardSummary>('/dashboard/summary'),

  emailTrends: (days = 30) =>
    apiClient.get<{ trends: EmailTrendPoint[] }>('/dashboard/email-trends', {
      params: { days },
    }),

  accountPerformance: () =>
    apiClient.get<{ accounts: AccountPerformance[] }>('/dashboard/account-performance'),
};
