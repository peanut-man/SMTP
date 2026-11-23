import apiClient from './client';
import type { EmailJob, EmailDetail } from '../types';

export const emailsApi = {
  send: (formData: FormData) =>
    apiClient.post<EmailJob>('/emails/send', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  get: (id: string) => apiClient.get<EmailDetail>(`/emails/${id}`),

  retry: (id: string) => apiClient.post<EmailJob>(`/emails/${id}/retry`),

  cancel: (id: string) => apiClient.post<EmailJob>(`/emails/${id}/cancel`),
};
