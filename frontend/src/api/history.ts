import apiClient from './client';
import type { EmailJob, PaginatedResponse } from '../types';

export interface HistoryFilters {
  page?: number;
  per_page?: number;
  status?: string;
  smtp_account_id?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
}

export const historyApi = {
  list: (filters: HistoryFilters = {}) =>
    apiClient.get<PaginatedResponse<EmailJob>>('/history', { params: filters }),

  get: (id: string) => apiClient.get<EmailJob>(`/history/${id}`),

  getAttempts: (id: string) => apiClient.get(`/history/${id}/attempts`),
};
