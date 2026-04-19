'use client'

import React, { useEffect, useState } from 'react'
import Cookies from 'js-cookie'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/components/providers/AuthProvider'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { useModelSettings, AIModel } from '@/components/providers/ModelSettingsProvider'
import { useLanguage, Language } from '@/components/providers/LanguageProvider'
import { PDFUploadForm } from '@/components/pdf/PDFUploadForm'
import { ConceptInputForm } from '@/components/pdf/ConceptInputForm'
import PPTUploadForm from '@/components/ppt-viewer/PPTUploadForm'

const API_BASE_URL =
  process.env.NODE_ENV === 'production'
    ? '/api'
    : process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

interface Document {
  id: number
  title: string
  original_filename: string
  page_count: number
  subject?: string
  grade_level?: number
  status: string
  created_at: string
  updated_at: string
  root_document_id?: number
  version_number: number
  is_current: number
  version_count: number
  user_prompt?: string
}

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const { selectedModel, setSelectedModel } = useModelSettings()
  const { language, setLanguage, t } = useLanguage()
  const router = useRouter()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [resourceType, setResourceType] = useState<'pdf' | 'ppt' | 'concept'>('pdf')
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false)
  const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false)
  const [showAllDocuments, setShowAllDocuments] = useState(false)

  const models: { value: AIModel; label: string; description: string }[] = [
    { value: 'glm-4.7', label: t('model.glm47'), description: t('model.glm47_desc') },
    { value: 'glm-4.6', label: t('model.glm46'), description: t('model.glm46_desc') },
    { value: 'claude-opus-4-6', label: t('model.opus46'), description: t('model.opus46_desc') },
    { value: 'claude-sonnet-4-6', label: t('model.sonnet46'), description: t('model.sonnet46_desc') },
    { value: 'claude-haiku-4-5-20251001', label: t('model.haiku45'), description: t('model.haiku45_desc') }
  ]

  const languages: { value: Language; label: string }[] = [
    { value: 'zh', label: '中文' },
    { value: 'en', label: 'English' },
  ]

  const getAuthToken = () => Cookies.get('access_token')

  const fetchDocuments = async () => {
    try {
      const token = getAuthToken()
      if (!token) throw new Error('Authentication required')

      const response = await fetch(`${API_BASE_URL}/pdf/documents?limit=100`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (!response.ok) throw new Error(`Failed to fetch documents: ${response.status}`)
      const data: Document[] = await response.json()
      setDocuments(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('dashboard.fetch_failed'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  const readyCount = documents.filter((doc) => doc.status === 'ready').length
  const processingCount = documents.filter((doc) => doc.status === 'processing').length
  const latestDocuments = [...documents].slice(0, 6)
  const displayedDocuments = showAllDocuments ? documents : latestDocuments
  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[radial-gradient(circle_at_15%_20%,_#f6f8ff_0%,_#ebefff_35%,_#e8ebf5_65%,_#e8eaef_100%)] [font-family:'Poppins','Noto_Sans_SC','PingFang_SC','Microsoft_YaHei',sans-serif]">
        <div className="w-full px-0 py-0">

          <div className="overflow-hidden rounded-none border-0 bg-white/30 shadow-none backdrop-blur-sm">
            <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[320px_minmax(0,1fr)]">
              <aside className="border-b border-slate-200/70 bg-white/78 p-5 backdrop-blur-sm lg:border-b-0 lg:border-r">
                <div className="mb-5 flex items-center px-2 py-2">
                  <img
                    src="/images/图标.jpg"
                    alt="MAIC-UI Logo"
                    className="mr-3 h-8 w-8 rounded-md object-cover"
                  />
                  <div className="text-[1.65rem] font-semibold tracking-tight text-slate-900">
                    {t('dashboard.title')}
                  </div>
                </div>

                <div className="mb-5 rounded-2xl border border-slate-200/80 bg-white/90 p-3">
                  <button
                    onClick={() =>
                      document.getElementById('upload-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                    }
                    className="mb-2 w-full rounded-xl bg-violet-50 px-3 py-2.5 text-left text-lg font-semibold text-violet-700"
                  >
                    {t('dashboard.interactive_resource')}
                  </button>
                  <button
                    onClick={() => router.push('/templates')}
                    className="mb-2 w-full rounded-xl px-3 py-2.5 text-left text-lg font-semibold text-slate-800 transition hover:bg-slate-50"
                  >
                    {t('dashboard.template_library')}
                  </button>
                  <button
                    onClick={() => router.push('/public_documents')}
                    className="w-full rounded-xl px-3 py-2.5 text-left text-lg font-semibold text-slate-800 transition hover:bg-slate-50"
                  >
                    {t('dashboard.view_public_docs')}
                  </button>
                </div>

                <div className="mb-5 grid grid-cols-3 gap-3">
                  <div className="rounded-xl border border-slate-200/80 bg-white/90 p-3">
                    <p className="text-xs text-slate-500">{t('dashboard.total_docs')}</p>
                    <p className="mt-1 text-xl font-semibold text-slate-900">{documents.length}</p>
                  </div>
                  <div className="rounded-xl border border-slate-200/80 bg-white/90 p-3">
                    <p className="text-xs text-slate-500">{t('dashboard.completed')}</p>
                    <p className="mt-1 text-xl font-semibold text-emerald-600">{readyCount}</p>
                  </div>
                  <div className="rounded-xl border border-slate-200/80 bg-white/90 p-3">
                    <p className="text-xs text-slate-500">{t('dashboard.processing')}</p>
                    <p className="mt-1 text-xl font-semibold text-amber-600">{processingCount}</p>
                  </div>
                </div>

                <div className="mb-5 rounded-2xl border border-slate-200/80 bg-white/90 p-3">
                  <p className="px-1 pb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t('dashboard.quick_access')}</p>
                  <div className="space-y-1">
                    <button
                      onClick={() =>
                        document.getElementById('upload-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                      }
                      className="flex w-full items-center rounded-lg px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-violet-50 hover:text-violet-700"
                    >
                      {t('dashboard.create_resource')}
                    </button>
                    <button
                      onClick={() =>
                        document
                          .getElementById('documents-panel')
                          ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                      }
                      className="flex w-full items-center rounded-lg px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-violet-50 hover:text-violet-700"
                    >
                      {t('dashboard.my_documents')}
                    </button>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-200/80 bg-white/90 p-3">
                  <p className="px-1 pb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t('dashboard.recent_docs')}</p>
                  <div className="space-y-2">
                    {latestDocuments.length === 0 ? (
                      <p className="px-2 py-3 text-xs text-slate-500">{t('dashboard.no_docs')}</p>
                    ) : (
                      latestDocuments.map((doc) => (
                        <button
                          key={`side-${doc.id}`}
                          onClick={() => window.open(`/document/${doc.id}`, '_blank')}
                          className="w-full rounded-lg border border-slate-200/80 bg-white px-2.5 py-2 text-left transition hover:border-violet-300 hover:bg-violet-50/70"
                        >
                          <p className="line-clamp-1 text-sm font-medium text-slate-800">{doc.title}</p>
                          <p className="mt-0.5 text-xs text-slate-500">
                            {doc.status === 'ready' ? t('dashboard.ready') : doc.status === 'processing' ? t('dashboard.processing_status') : t('dashboard.error_status')}
                          </p>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              </aside>

              <main className="bg-gradient-to-b from-white/78 to-white/52 p-5 sm:p-6 lg:p-8">
                <div className="rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-[0_14px_40px_rgba(40,50,90,0.08)] sm:p-6">
                  <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-center gap-3">
                      {/* Language Selector */}
                      <div className="relative">
                        <button
                          type="button"
                          onClick={() => setIsLanguageDropdownOpen((prev) => !prev)}
                          className="flex items-center justify-between rounded-2xl border border-slate-300 bg-white px-4 py-2.5 text-left text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                        >
                          <span className="font-semibold">{languages.find(l => l.value === language)?.label}</span>
                          <svg
                            className={`ml-2 h-4 w-4 transition-transform ${isLanguageDropdownOpen ? 'rotate-180' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>

                        {isLanguageDropdownOpen && (
                          <div className="absolute left-0 z-50 mt-2 w-[120px] overflow-hidden rounded-2xl border border-slate-300 bg-white shadow-lg">
                            {languages.map((lang) => (
                              <button
                                key={lang.value}
                                type="button"
                                onClick={() => {
                                  setLanguage(lang.value)
                                  setIsLanguageDropdownOpen(false)
                                }}
                                className={`w-full border-l-4 px-4 py-3 text-left transition hover:bg-slate-50 ${
                                  language === lang.value ? 'border-violet-600 bg-violet-50' : 'border-transparent'
                                }`}
                              >
                                <div className="flex items-center justify-between">
                                  <span className="font-semibold text-slate-900">{lang.label}</span>
                                  {language === lang.value && (
                                    <svg className="h-5 w-5 text-violet-600" fill="currentColor" viewBox="0 0 20 20">
                                      <path
                                        fillRule="evenodd"
                                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                        clipRule="evenodd"
                                      />
                                    </svg>
                                  )}
                                </div>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Model Selector */}
                      <div className="relative">
                        <button
                          type="button"
                          onClick={() => setIsModelDropdownOpen((prev) => !prev)}
                          className="flex items-center justify-between rounded-2xl border border-slate-300 bg-white px-4 py-2.5 text-left text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                        >
                          <span className="text-slate-600">{t('dashboard.ai_model')}:</span>
                          <span className="ml-1 font-semibold text-violet-600">{selectedModel}</span>
                          <svg
                            className={`ml-2 h-4 w-4 transition-transform ${isModelDropdownOpen ? 'rotate-180' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>

                        {isModelDropdownOpen && (
                          <div className="absolute left-0 z-50 mt-2 w-[260px] overflow-hidden rounded-2xl border border-slate-300 bg-white shadow-lg">
                            {models.map((model) => (
                              <button
                                key={model.value}
                                type="button"
                                onClick={() => {
                                  setSelectedModel(model.value)
                                  setIsModelDropdownOpen(false)
                                }}
                                className={`w-full border-l-4 px-4 py-3 text-left transition hover:bg-slate-50 ${
                                  selectedModel === model.value ? 'border-violet-600 bg-violet-50' : 'border-transparent'
                                }`}
                              >
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-[17px] font-semibold text-slate-900">{model.label}</p>
                                    <p className="mt-1 text-xs text-slate-500">{model.description}</p>
                                  </div>
                                  {selectedModel === model.value && (
                                    <svg className="h-5 w-5 text-violet-600" fill="currentColor" viewBox="0 0 20 20">
                                      <path
                                        fillRule="evenodd"
                                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                        clipRule="evenodd"
                                      />
                                    </svg>
                                  )}
                                </div>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="w-full sm:w-auto">
                      <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
                        <div className="flex items-center justify-between gap-3">
                          <p className="font-semibold text-slate-900">{t('dashboard.login_info')}</p>
                          <button
                            onClick={handleLogout}
                            className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 transition hover:bg-slate-50"
                          >
                            {t('dashboard.logout')}
                          </button>
                        </div>
                        <p className="mt-1">{t('dashboard.user')}: {user?.username || t('dashboard.not_logged_in')}</p>
                        <p className="text-slate-500">{user?.email || '-'}</p>
                        {loading && <p className="mt-1 text-xs text-slate-400">{t('dashboard.loading')}</p>}
                      </div>
                    </div>
                  </div>

                  <div className="mb-8 text-center">
                    <p className="text-3xl font-semibold tracking-tight text-slate-900">
                      {t('dashboard.welcome')}
                    </p>
                    <p className="mt-2 text-2xl font-semibold text-slate-800">
                      {t('dashboard.select_method')}
                    </p>
                  </div>

                  <div id="upload-panel" className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-3">
                    <button
                      onClick={() => setResourceType('pdf')}
                      className={`rounded-2xl border p-5 text-left transition ${
                        resourceType === 'pdf'
                          ? 'border-[#7C4DFF] bg-[#f5f0ff] shadow-[0_10px_24px_rgba(124,77,255,0.2)]'
                          : 'border-slate-200 bg-white hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <img src="/icons/PDF-lite.png" alt="PDF" className="h-12 w-12 rounded-lg object-contain" />
                        <div>
                          <p className="text-xl font-semibold text-slate-900">{t('dashboard.upload_pdf')}</p>
                          <p className="mt-2 text-sm text-slate-500">{t('dashboard.from_material')}</p>
                        </div>
                      </div>
                    </button>

                    <button
                      onClick={() => setResourceType('ppt')}
                      className={`rounded-2xl border p-5 text-left transition ${
                        resourceType === 'ppt'
                          ? 'border-[#7C4DFF] bg-[#f5f0ff] shadow-[0_10px_24px_rgba(124,77,255,0.2)]'
                          : 'border-slate-200 bg-white hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <img src="/icons/PPT-lite.png" alt="PPT" className="h-12 w-12 rounded-lg object-contain" />
                        <div>
                          <p className="text-xl font-semibold text-slate-900">{t('dashboard.upload_ppt')}</p>
                          <p className="mt-2 text-sm text-slate-500">{t('dashboard.from_presentation')}</p>
                        </div>
                      </div>
                    </button>

                    <button
                      onClick={() => setResourceType('concept')}
                      className={`rounded-2xl border p-5 text-left transition ${
                        resourceType === 'concept'
                          ? 'border-[#7C4DFF] bg-[#f4efff] shadow-[0_10px_24px_rgba(124,77,255,0.18)]'
                          : 'border-slate-200 bg-white hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <img src="/icons/idea-lite.png" alt="idea" className="h-12 w-12 rounded-lg object-contain" />
                        <div>
                          <p className="text-xl font-semibold text-slate-900">{t('dashboard.input_concept')}</p>
                          <p className="mt-2 text-sm text-slate-500">{t('dashboard.custom_generate')}</p>
                        </div>
                      </div>
                    </button>
                  </div>

                  <div>
                    {resourceType === 'pdf' && <PDFUploadForm hideTypeSelector initialType="pdf" />}
                    {resourceType === 'ppt' && <PPTUploadForm embedded />}
                    {resourceType === 'concept' && <ConceptInputForm />}
                  </div>

                  <div id="documents-panel" className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                    <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                      <h3 className="text-xl font-semibold text-slate-900">{t('dashboard.my_documents')}</h3>
                      <button
                        onClick={() => setShowAllDocuments((prev) => !prev)}
                        className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                      >
                        {showAllDocuments ? t('dashboard.collapse') : t('dashboard.show_all')}
                      </button>
                    </div>
                    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                      {displayedDocuments.length === 0 ? (
                        <p className="text-sm text-slate-500">{t('dashboard.no_docs')}</p>
                      ) : (
                        displayedDocuments.map((doc) => (
                          <button
                            key={`main-${doc.id}`}
                            onClick={() => window.open(`/document/${doc.id}`, '_blank')}
                            className="rounded-xl border border-slate-200 bg-white p-3 text-left transition hover:border-violet-300 hover:bg-violet-50/60"
                          >
                            <p className="line-clamp-1 text-base font-medium text-slate-900">{doc.title}</p>
                            <p className="mt-1 text-xs text-slate-500">
                              {doc.status === 'ready' ? t('dashboard.ready') : doc.status === 'processing' ? t('dashboard.processing_status') : t('dashboard.error_status')}
                            </p>
                          </button>
                        ))
                      )}
                    </div>
                  </div>

                  {error && (
                    <div className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-red-700">
                      {t('dashboard.error_prefix')}{error}
                    </div>
                  )}
                </div>
              </main>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}