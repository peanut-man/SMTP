import apiClient from './client';
import type { Contact, PaginatedResponse, ContactImportResult } from '../types';

export interface ContactFilters {
  page?: number;
  per_page?: number;
  search?: string;
  group?: string;
}

export const contactsApi = {
  list: (filters: ContactFilters = {}) =>
    apiClient.get<PaginatedResponse<Contact>>('/contacts', { params: filters }),

  get: (id: string) => apiClient.get<Contact>(`/contacts/${id}`),

  create: (data: Partial<Contact>) => apiClient.post<Contact>('/contacts', data),

  update: (id: string, data: Partial<Contact>) => apiClient.put<Contact>(`/contacts/${id}`, data),

  delete: (id: string) => apiClient.delete(`/contacts/${id}`),

  import: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post<ContactImportResult>('/contacts/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  export: () =>
    apiClient.get('/contacts/export', {
      responseType: 'blob',
    }),
};
