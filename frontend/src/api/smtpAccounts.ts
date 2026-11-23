import apiClient from './client';
import type { SMTPAccount, SMTPTestResult } from '../types';

export const smtpAccountsApi = {
  list: () => apiClient.get<SMTPAccount[]>('/smtp-accounts'),

  get: (id: string) => apiClient.get<SMTPAccount>(`/smtp-accounts/${id}`),

  create: (data: Partial<SMTPAccount> & { password: string }) =>
    apiClient.post<SMTPAccount>('/smtp-accounts', data),

  update: (id: string, data: Partial<SMTPAccount> & { password?: string }) =>
    apiClient.put<SMTPAccount>(`/smtp-accounts/${id}`, data),

  delete: (id: string) => apiClient.delete(`/smtp-accounts/${id}`),

  test: (id: string) => apiClient.post<SMTPTestResult>(`/smtp-accounts/${id}/test`),

  setDefault: (id: string) => apiClient.post<SMTPAccount>(`/smtp-accounts/${id}/set-default`),
};
