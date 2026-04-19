/**
 * Template API Service
 *
 * Handles all API calls for template-based content generation.
 */

import Cookies from 'js-cookie';
import type {
  TemplateSearchResult,
  TemplateGenerateResult,
  TemplatePreviewResult,
  TemplateBrowseResult,
  TemplateCategoriesResult,
  WorkflowTypesResult,
  TemplateBrowseFilters,
  PPTTemplateSelection,
  PPTStatusWithTemplates,
  PPTContentInfo,
  WebsitePDFContentInfo,
  WebsiteConceptContentInfo
} from '../lib/templateTypes';

// In production, use relative path /api; in development use localhost:8000/api
const API_URL = process.env.NODE_ENV === 'production' ? '/api' : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api');

// Helper to build API URLs
const buildUrl = (path: string) => `${API_URL}${path}`;

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
 * Universal template search endpoint
 */
export async function searchTemplates(
  workflowType: 'ppt_demo' | 'website_pdf' | 'website_concept',
  contentInfo: PPTContentInfo | WebsitePDFContentInfo | WebsiteConceptContentInfo,
  maxResults: number = 5
): Promise<TemplateSearchResult> {
  const response = await fetch(buildUrl('/templates/search'), {
    method: 'POST',
    headers: {
      ...getAuthHeader(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      workflow_type: workflowType,
      content_info: contentInfo,
      max_results: maxResults,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Template search failed');
  }

  return response.json();
}

/**
 * Universal template generation endpoint
 */
export async function generateWithTemplate(
  templateId: string,
  workflowType: 'ppt_demo' | 'website_pdf' | 'website_concept',
  contentInfo: Record<string, any>,
  userPreferences: Record<string, any>,
  customizationParams?: Record<string, any>
): Promise<TemplateGenerateResult> {
  const response = await fetch(buildUrl('/templates/generate'), {
    method: 'POST',
    headers: {
      ...getAuthHeader(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      template_id: templateId,
      workflow_type: workflowType,
      content_info: contentInfo,
      user_preferences: userPreferences,
      customization_params: customizationParams,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Template generation failed');
  }

  return response.json();
}

/**
 * Preview template HTML
 * Public endpoint - no authentication required
 */
export async function previewTemplate(templateId: string): Promise<TemplatePreviewResult> {
  const response = await fetch(buildUrl(`/templates/${templateId}/preview`));

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to preview template');
  }

  return response.json();
}

/**
 * Browse templates with filters
 * Public endpoint - no authentication required
 */
export async function browseTemplates(filters?: TemplateBrowseFilters): Promise<TemplateBrowseResult> {
  const params = new URLSearchParams();

  if (filters?.workflow_type) params.append('workflow_type', filters.workflow_type);
  if (filters?.category) params.append('category', filters.category);
  if (filters?.grade_level) params.append('grade_level', filters.grade_level.toString());
  if (filters?.subject_area) params.append('subject_area', filters.subject_area);
  if (filters?.complexity) params.append('complexity', filters.complexity);
  if (filters?.limit) params.append('limit', filters.limit.toString());

  const response = await fetch(
    buildUrl(`/templates/browse?${params.toString()}`)
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to browse templates');
  }

  return response.json();
}

/**
 * Get available template categories
 * Public endpoint - no authentication required
 */
export async function getTemplateCategories(): Promise<TemplateCategoriesResult> {
  const response = await fetch(buildUrl('/templates/categories'));

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get categories');
  }

  return response.json();
}

/**
 * Get supported workflow types
 * Public endpoint - no authentication required
 */
export async function getWorkflowTypes(): Promise<WorkflowTypesResult> {
  const response = await fetch(buildUrl('/templates/workflow-types'));

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get workflow types');
  }

  return response.json();
}

// ==================== PPT-Specific Endpoints ====================

/**
 * Select templates for PPT slides and generate demos
 */
export async function selectPPTTemplates(
  documentId: number,
  templateSelections: PPTTemplateSelection
): Promise<any> {
  const response = await fetch(buildUrl(`/ppt/documents/${documentId}/select-templates`), {
    method: 'POST',
    headers: {
      ...getAuthHeader(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(templateSelections),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Template selection failed');
  }

  return response.json();
}

/**
 * Get PPT document status (includes template options when awaiting selection)
 */
export async function getPPTStatusWithTemplates(documentId: number): Promise<PPTStatusWithTemplates> {
  const response = await fetch(buildUrl(`/ppt/documents/${documentId}/status`), {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to get PPT status');
  }

  return response.json();
}

// ==================== Website-Specific Endpoints ====================

/**
 * Search templates for concept-based website generation
 */
export async function searchConceptTemplates(
  subject: string,
  conceptName: string,
  conceptOverview: string,
  gradeLevel?: number,
  maxResults: number = 5
): Promise<TemplateSearchResult> {
  const formData = new FormData();
  formData.append('subject', subject);
  formData.append('concept_name', conceptName);
  formData.append('concept_overview', conceptOverview);
  if (gradeLevel) formData.append('grade_level', gradeLevel.toString());
  formData.append('max_results', maxResults.toString());

  const response = await fetch(buildUrl('/pdf/concept/search-templates'), {
    method: 'POST',
    headers: getAuthHeader(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Concept template search failed');
  }

  return response.json();
}

/**
 * Generate website from concept using template
 */
export async function generateConceptWithTemplate(
  subject: string,
  conceptName: string,
  conceptOverview: string,
  masteryPoints: string,
  designIdea: string,
  templateId: string,
  gradeLevel?: number,
  description?: string,
  isPublic?: boolean,
  interests?: string,
  customizationParams?: Record<string, any>
): Promise<any> {
  const formData = new FormData();
  formData.append('subject', subject);
  formData.append('concept_name', conceptName);
  formData.append('concept_overview', conceptOverview);
  formData.append('mastery_points', masteryPoints);
  formData.append('design_idea', designIdea);
  formData.append('template_id', templateId);
  if (gradeLevel) formData.append('grade_level', gradeLevel.toString());
  if (description) formData.append('description', description);
  if (isPublic !== undefined) formData.append('is_public', isPublic.toString());
  if (interests) formData.append('interests', interests);
  if (customizationParams) {
    formData.append('customization_params', JSON.stringify(customizationParams));
  }

  const response = await fetch(buildUrl('/pdf/concept/generate-with-template'), {
    method: 'POST',
    headers: getAuthHeader(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Concept generation failed');
  }

  return response.json();
}

/**
 * Search templates for PDF document
 */
export async function searchPDFTemplates(
  documentId: number,
  maxResults: number = 5
): Promise<TemplateSearchResult> {
  const formData = new FormData();
  formData.append('max_results', maxResults.toString());

  const response = await fetch(buildUrl(`/pdf/pdf/${documentId}/search-templates`), {
    method: 'POST',
    headers: getAuthHeader(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'PDF template search failed');
  }

  return response.json();
}

/**
 * Regenerate PDF website using template
 */
export async function generatePDFWithTemplate(
  documentId: number,
  templateId: string,
  customizationParams?: Record<string, any>
): Promise<any> {
  const formData = new FormData();
  formData.append('template_id', templateId);
  if (customizationParams) {
    formData.append('customization_params', JSON.stringify(customizationParams));
  }

  const response = await fetch(buildUrl(`/pdf/pdf/${documentId}/generate-with-template`), {
    method: 'POST',
    headers: getAuthHeader(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'PDF template generation failed');
  }

  return response.json();
}
