// All TypeScript interfaces for the SMTP Mail Management Platform

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface SMTPAccount {
  id: string;
  account_name: string;
  smtp_host: string;
  smtp_port: number;
  username: string;
  security_mode: 'STARTTLS' | 'SSL_TLS' | 'PLAIN';
  sender_email: string;
  sender_name: string;
  connection_timeout: number;
  is_default: boolean;
  is_active: boolean;
  last_tested_at: string | null;
  last_test_status: 'success' | 'failed' | 'untested';
  last_test_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface SMTPTestResult {
  success: boolean;
  message: string;
  details: string | null;
  tested_at: string;
}

export type JobStatus = 'PENDING' | 'PROCESSING' | 'ACCEPTED' | 'FAILED' | 'RETRYING' | 'CANCELLED';

export interface EmailJob {
  id: string;
  subject: string;
  sender_email: string;
  sender_name: string | null;
  reply_to: string | null;
  recipient_count: number;
  message_type: 'direct' | 'template' | 'test';
  status: JobStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  last_error: string | null;
  retry_count: number;
  max_retries: number;
  next_retry_at: string | null;
  smtp_account_id: string;
}

export interface EmailRecipient {
  id: string;
  recipient_email: string;
  recipient_name: string | null;
  recipient_type: 'to' | 'cc' | 'bcc';
  status: string;
  smtp_response: string | null;
}

export interface EmailAttempt {
  id: string;
  attempt_number: number;
  status: 'success' | 'failed' | 'timeout';
  smtp_response_code: number | null;
  smtp_response_message: string | null;
  error_message: string | null;
  attempted_at: string;
  completed_at: string | null;
}

export interface EmailDetail {
  job: EmailJob;
  recipients: EmailRecipient[];
  attempts: EmailAttempt[];
}

export interface EmailTemplate {
  id: string;
  name: string;
  description: string | null;
  subject: string;
  html_content: string | null;
  text_content: string | null;
  variables: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface Contact {
  id: string;
  name: string;
  email: string;
  organization: string | null;
  group_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardSummary {
  total_emails: number;
  accepted_emails: number;
  failed_emails: number;
  pending_emails: number;
  retrying_emails: number;
  cancelled_emails: number;
  active_smtp_accounts: number;
  total_smtp_accounts: number;
  total_contacts: number;
  total_templates: number;
}

export interface EmailTrendPoint {
  date: string;
  submitted: number;
  accepted: number;
  failed: number;
}

export interface AccountPerformance {
  account_id: string;
  account_name: string;
  smtp_host: string;
  total_sent: number;
  accepted: number;
  failed: number;
  success_rate: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface RecipientItem {
  email: string;
  name?: string;
  type: 'to' | 'cc' | 'bcc';
}

export interface SendEmailPayload {
  smtp_account_id: string;
  subject: string;
  recipients: RecipientItem[];
  html_body?: string;
  text_body?: string;
  reply_to?: string;
  template_id?: string;
  template_variables?: Record<string, string>;
}

export interface ContactImportResult {
  imported: number;
  skipped: number;
  errors: string[];
}
