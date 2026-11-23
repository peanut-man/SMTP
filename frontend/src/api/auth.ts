import apiClient from './client';
import type { TokenResponse, User } from '../types';

export const authApi = {
  register: (data: { username: string; email: string; password: string }) =>
    apiClient.post<TokenResponse>('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    apiClient.post<TokenResponse>('/auth/login', data),

  logout: () => apiClient.post('/auth/logout'),

  me: () => apiClient.get<User>('/auth/me'),
};
