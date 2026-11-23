import apiClient from './client';
import type { EmailTemplate } from '../types';

export const templatesApi = {
  list: () => apiClient.get<EmailTemplate[]>('/templates'),

  get: (id: string) => apiClient.get<EmailTemplate>(`/templates/${id}`),

  create: (data: Partial<EmailTemplate>) => apiClient.post<EmailTemplate>('/templates', data),

  update: (id: string, data: Partial<EmailTemplate>) =>
    apiClient.put<EmailTemplate>(`/templates/${id}`, data),

  delete: (id: string) => apiClient.delete(`/templates/${id}`),

  preview: (id: string, variables: Record<string, string>) =>
    apiClient.post(`/templates/${id}/preview`, { variables }),
};
