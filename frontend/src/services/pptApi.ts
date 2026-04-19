/**
 * PPT API Service
 *
 * Handles all API calls for PPT presentation processing and viewing.
 */

import Cookies from 'js-cookie';

// In production, use relative path /api; in development use localhost:8000/api
const API_URL = process.env.NODE_ENV === 'production' ? '/api' : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api');

// Helper to build API URLs
const buildUrl = (path: string) => `${API_URL}${path}`;

export interface PPTUploadMetadata {
  title: string;
  subject?: string;
  grade_level?: number;
  description?: string;
  is_public?: boolean;
}

export interface PPTDocument {
  id: number;
  title: string;
  original_filename: string;
  file_type: string;
  slide_count: number;
  subject?: string;
  grade_level?: number;
  description?: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface Slide {
  slide_number: number;
  image_path: string;
  title: string;
  description: string;
  needs_demo: boolean;
  demo_html?: string;
  demo_reason?: string;
  demo_type?: string;
}

export interface PPTDocumentDetail extends PPTDocument {
  slides?: Slide[];
  analysis?: any;
  error_message?: string;
}

export interface SlideItem {
  type: 'slide';
  slide_number: number;
  image_path: string;
  title: string;
  description: string;
}

export interface DemoItem {
  type: 'demo';
  slide_number: number;
  html: string;
  reason: string;
  demo_type: string;
}

export type InteractiveItem = SlideItem | DemoItem;

export interface InteractiveView {
  document_id: number;
  title: string;
  subject: string;
  grade_level: number;
  total_items: number;
  items: InteractiveItem[];
}

/**
 * Get auth token from cookies
 */
function getAuthHeader(): HeadersInit {
  const token = typeof window !== 'undefined' ? Cookies.get('access_token') : null;
  return {
    'Authorization': `Bearer ${token}`,
  };
}

/**
 * Upload a PPT/PPTX/PDF file for processing
 */
export async function uploadPPT(
  file: File,
  metadata: PPTUploadMetadata
): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', metadata.title);

  // Detect file type from filename
  const extension = file.name.split('.').pop()?.toLowerCase();
  formData.append('file_type', extension === 'pptx' ? 'pptx' : 'pdf');

  if (metadata.subject) formData.append('subject', metadata.subject);
  if (metadata.grade_level) formData.append('grade_level', metadata.grade_level.toString());
  if (metadata.description) formData.append('description', metadata.description);
  if (metadata.is_public !== undefined) formData.append('is_public', metadata.is_public.toString());

  const response = await fetch(buildUrl('/ppt/upload'), {
    method: 'POST',
    headers: getAuthHeader(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

/**
 * Get list of user's PPT documents
 */
export async function getPPTDocuments(skip: number = 0, limit: number = 20): Promise<PPTDocument[]> {
  const response = await fetch(
    buildUrl(`/ppt/documents?skip=${skip}&limit=${limit}`),
    {
      headers: getAuthHeader(),
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch documents');
  }

  return response.json();
}

/**
 * Get specific PPT document details
 */
export async function getPPTDocument(documentId: number): Promise<PPTDocumentDetail> {
  const response = await fetch(buildUrl(`/ppt/documents/${documentId}`), {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch document');
  }

  return response.json();
}

/**
 * Get all slides for a document
 */
export async function getPPTSlides(documentId: number): Promise<{
  document_id: number;
  title: string;
  slides: Slide[];
}> {
  const response = await fetch(buildUrl(`/ppt/documents/${documentId}/slides`), {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch slides');
  }

  return response.json();
}

/**
 * Get interactive view (slides with demos interspersed)
 */
export async function getInteractiveView(documentId: number): Promise<InteractiveView> {
  const response = await fetch(
    buildUrl(`/ppt/documents/${documentId}/interactive-view`),
    {
      headers: getAuthHeader(),
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch interactive view');
  }

  return response.json();
}

/**
 * Get processing status of a document
 */
export async function getPPTStatus(documentId: number): Promise<{
  document_id: number;
  status: string;
  progress: number;
  message: string;
  slide_count: number;
  template_options?: Record<number, Array<{
    template_id: string;
    display_name: string;
    match_score: number;
    match_reason: string;
    complexity?: string;
    subject_area?: string;
    usage_count?: number;
  }>>;
}> {
  const response = await fetch(
    buildUrl(`/ppt/documents/${documentId}/status`),
    {
      headers: getAuthHeader(),
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch status');
  }

  return response.json();
}

/**
 * Get public PPT documents
 */
export async function getPublicPPTDocuments(skip: number = 0, limit: number = 20): Promise<PPTDocument[]> {
  const response = await fetch(
    buildUrl(`/ppt/public/documents?skip=${skip}&limit=${limit}`)
  );

  if (!response.ok) {
    throw new Error('Failed to fetch public documents');
  }

  return response.json();
}

/**
 * Get public PPT document details
 */
export async function getPublicPPTDocument(documentId: number): Promise<PPTDocumentDetail> {
  const response = await fetch(buildUrl(`/ppt/public/documents/${documentId}`));

  if (!response.ok) {
    throw new Error('Failed to fetch public document');
  }

  return response.json();
}

/**
 * Get public interactive view
 */
export async function getPublicInteractiveView(documentId: number): Promise<InteractiveView> {
  const response = await fetch(
    buildUrl(`/ppt/public/documents/${documentId}/interactive-view`)
  );

  if (!response.ok) {
    throw new Error('Failed to fetch public interactive view');
  }

  return response.json();
}

/**
 * Delete a PPT document
 */
export async function deletePPTDocument(documentId: number): Promise<{ message: string }> {
  const response = await fetch(buildUrl(`/ppt/documents/${documentId}`), {
    method: 'DELETE',
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to delete document');
  }

  return response.json();
}
