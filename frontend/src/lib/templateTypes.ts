/**
 * Template Types
 *
 * Type definitions for the Template-Based Demo Library system.
 */

export interface Template {
  template_id: string;
  display_name: string;
  name: string;
  workflow_type: 'ppt_demo' | 'website_pdf' | 'website_concept';
  complexity?: 'simple' | 'medium' | 'complex';
  subject_area?: string;
  usage_count?: number;
  thumbnail?: string;
}

export interface TemplateOption extends Template {
  match_score: number;
  match_reason: string;
  demo_reason?: string;
  demo_type?: string;
}

export interface TemplateSearchResult {
  status: string;
  workflow_type: string;
  templates_found: number;
  template_options: TemplateOption[];
}

export interface TemplateGenerateRequest {
  template_id: string;
  workflow_type: 'ppt_demo' | 'website_pdf' | 'website_concept';
  content_info: Record<string, any>;
  user_preferences: Record<string, any>;
  customization_params?: Record<string, any>;
}

export interface TemplateGenerateResult {
  status: string;
  html?: string;
  metadata?: {
    template_used?: string;
    generation_method?: string;
    template_name?: string;
  };
  error?: string;
}

export interface TemplatePreviewResult {
  template_id: string;
  display_name: string;
  name: string;
  workflow_type: string;
  html: string;
}

export interface TemplateBrowseFilters {
  workflow_type?: 'ppt_demo' | 'website_pdf' | 'website_concept';
  category?: string;
  grade_level?: number;
  subject_area?: string;
  complexity?: 'simple' | 'medium' | 'complex';
  limit?: number;
}

export interface TemplateBrowseResult {
  status: string;
  count: number;
  templates: Template[];
}

export interface TemplateCategoriesResult {
  status: string;
  categories: string[];
}

export interface WorkflowType {
  type: string;
  display_name: string;
  description: string;
}

export interface WorkflowTypesResult {
  status: string;
  workflow_types: WorkflowType[];
}

// PPT-specific types
export interface PPTTemplateSelection {
  [slideNumber: string]: string; // slide_number -> template_id
}

export interface PPTTemplateOptions {
  [slideNumber: number]: TemplateOption[]; // slide_number -> template_options
}

export interface PPTStatusWithTemplates {
  document_id: number;
  status: string;
  progress: number;
  message: string;
  slide_count: number;
  template_options?: PPTTemplateOptions;
}

// Content info types for different workflows
export interface PPTContentInfo {
  title: string;
  description?: string;
  demo_type?: string;
  grade_level?: number;
  subject?: string;
}

export interface WebsitePDFContentInfo {
  title: string;
  description?: string;
  subject?: string;
  grade_level?: number;
  category?: string;
}

export interface WebsiteConceptContentInfo {
  title: string;
  description: string;
  subject: string;
  grade_level?: number;
  mastery_points?: string;
  design_idea?: string;
}
