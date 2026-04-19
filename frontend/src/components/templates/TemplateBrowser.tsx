'use client'

import { useEffect, useState } from 'react'
import { browseTemplates, getTemplateCategories } from '../../services/templateApi'
import type { Template, TemplateBrowseFilters } from '../../lib/templateTypes'
import { useLanguage } from '../providers/LanguageProvider'

interface TemplateBrowserProps {
  workflowType?: 'ppt_demo' | 'website_pdf' | 'website_concept'
}

export default function TemplateBrowser({ workflowType }: TemplateBrowserProps) {
  const { language, t } = useLanguage()
  const [templates, setTemplates] = useState<Template[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [selectedComplexity, setSelectedComplexity] = useState<string>('')
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>(workflowType || '')

  useEffect(() => {
    loadTemplates()
    loadCategories()
  }, [selectedCategory, selectedComplexity, selectedWorkflow])

  const loadTemplates = async () => {
    try {
      setLoading(true)
      setError(null)

      const filters: TemplateBrowseFilters = {
        workflow_type: (selectedWorkflow as any) || undefined,
        category: selectedCategory || undefined,
        complexity: (selectedComplexity as any) || undefined,
        limit: 20
      }

      const result = await browseTemplates(filters)
      setTemplates(result.templates)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('templates.load_failed'))
    } finally {
      setLoading(false)
    }
  }

  const loadCategories = async () => {
    try {
      const result = await getTemplateCategories()
      setCategories(result.categories)
    } catch (err) {
      console.error('Failed to load categories:', err)
    }
  }

  const getComplexityStyle = (complexity?: string) => {
    switch (complexity) {
      case 'simple':
        return 'bg-emerald-100 text-emerald-700'
      case 'medium':
        return 'bg-amber-100 text-amber-700'
      case 'complex':
        return 'bg-rose-100 text-rose-700'
      default:
        return 'bg-slate-100 text-slate-700'
    }
  }

  const getComplexityText = (complexity?: string) => {
    switch (complexity) {
      case 'simple':
        return t('templates.simple')
      case 'medium':
        return t('templates.medium')
      case 'complex':
        return t('templates.complex')
      default:
        return t('templates.unknown')
    }
  }

  const getWorkflowTypeText = (type: string) => {
    switch (type) {
      case 'ppt_demo':
        return t('templates.ppt_demo')
      case 'website_pdf':
        return t('templates.website_pdf')
      case 'website_concept':
        return t('templates.website_concept')
      default:
        return type
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">{t('templates.workflow_type')}</label>
            <select
              value={selectedWorkflow}
              onChange={(e) => setSelectedWorkflow(e.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:ring-2 focus:ring-violet-300"
            >
              <option value="">{t('templates.all')}</option>
              <option value="ppt_demo">{t('templates.ppt_demo')}</option>
              <option value="website_pdf">{t('templates.website_pdf')}</option>
              <option value="website_concept">{t('templates.website_concept')}</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">{t('templates.category')}</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:ring-2 focus:ring-violet-300"
            >
              <option value="">{t('templates.all')}</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">{t('templates.complexity')}</label>
            <select
              value={selectedComplexity}
              onChange={(e) => setSelectedComplexity(e.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:ring-2 focus:ring-violet-300"
            >
              <option value="">{t('templates.all')}</option>
              <option value="simple">{t('templates.simple')}</option>
              <option value="medium">{t('templates.medium')}</option>
              <option value="complex">{t('templates.complex')}</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => {
                setSelectedCategory('')
                setSelectedComplexity('')
                setSelectedWorkflow(workflowType || '')
              }}
              className="w-full rounded-xl bg-slate-100 px-4 py-2 text-slate-700 transition hover:bg-slate-200"
            >
              {t('templates.reset_filter')}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4">
          <p className="text-sm text-rose-700">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <svg className="h-8 w-8 animate-spin text-violet-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </div>
      ) : (
        <>
          <div className="text-sm text-slate-600">{t('templates.found_count', { count: templates.length })}</div>

          {templates.length === 0 ? (
            <div className="rounded-xl bg-slate-50 py-12 text-center">
              <p className="text-slate-600">{t('templates.no_match')}</p>
              <p className="mt-2 text-sm text-slate-500">{t('templates.adjust_filter')}</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {templates.map((template) => (
                <div
                  key={template.template_id}
                  className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md"
                >
                  <div className="mb-4 flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <h3 className="line-clamp-2 font-semibold text-slate-900" style={{ fontSize: 'clamp(1.05rem, 0.55vw + 0.9rem, 1.45rem)' }}>
                        {template.display_name}
                      </h3>
                      <p className="mt-1 line-clamp-1 text-sm text-slate-500">{template.name}</p>
                    </div>
                    <div className="flex flex-col gap-2">
                      <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">{t('templates.public')}</span>
                      <span className="rounded-full bg-violet-100 px-3 py-1 text-xs font-medium text-violet-700">{t('templates.template')}</span>
                      {template.complexity && (
                        <span className={`rounded-full px-3 py-1 text-xs font-medium ${getComplexityStyle(template.complexity)}`}>
                          {getComplexityText(template.complexity)}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mb-5 space-y-2 text-sm text-slate-600">
                    <div className="flex justify-between">
                      <span>{t('templates.type')}</span>
                      <span className="font-medium text-slate-900">{getWorkflowTypeText(template.workflow_type)}</span>
                    </div>
                    {template.subject_area && (
                      <div className="flex justify-between">
                        <span>{t('templates.subject')}</span>
                        <span className="font-medium text-slate-900">{template.subject_area}</span>
                      </div>
                    )}
                    {template.usage_count !== undefined && (
                      <div className="flex justify-between">
                        <span>{t('templates.usage_count')}</span>
                        <span className="font-medium text-slate-900">{template.usage_count}</span>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => window.open(`/templates/preview/${template.template_id}`, '_blank')}
                    className="w-full rounded-lg bg-gradient-to-r from-violet-600 to-purple-500 px-4 py-2 text-base font-semibold text-white shadow-[0_6px_16px_rgba(124,77,255,0.26)] transition hover:brightness-105"
                  >
                    {t('templates.preview')}
                  </button>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
