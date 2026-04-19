'use client'

import React, { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/components/providers/AuthProvider'
import { useLanguage, Language } from '@/components/providers/LanguageProvider'

const API_BASE_URL =
  process.env.NODE_ENV === 'production'
    ? '/api'
    : process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

interface PublicDocument {
  id: number
  title: string
  original_filename: string
  page_count: number
  subject?: string
  grade_level?: number
  description?: string
  status: string
  created_at: string
  updated_at: string
  document_type: 'pdf' | 'ppt' | 'concept'
  root_document_id?: number | null
  version_number?: number
  is_current?: number
}

interface DocumentGroup {
  rootDocument: PublicDocument
  versions: PublicDocument[]
}

export default function PublicDocumentsPage() {
  const router = useRouter()
  const { user, logout } = useAuth()
  const { language, setLanguage, t } = useLanguage()

  const [documents, setDocuments] = useState<PublicDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [documentTypeFilter, setDocumentTypeFilter] = useState<'all' | 'pdf' | 'ppt' | 'concept'>('all')
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())
  const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false)

  const languages: { value: Language; label: string }[] = [
    { value: 'zh', label: '中文' },
    { value: 'en', label: 'English' },
  ]

  const normalizeDateForApi = (value: string) => {
    const normalized = value.trim().replace(/\//g, '-')
    return /^\d{4}-\d{2}-\d{2}$/.test(normalized) ? normalized : ''
  }

  const fetchPublicDocuments = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      const fromDateApi = normalizeDateForApi(dateFrom)
      const toDateApi = normalizeDateForApi(dateTo)
      if (fromDateApi) params.append('date_from', fromDateApi)
      if (toDateApi) params.append('date_to', toDateApi)
      params.append('limit', '1000')
      const queryString = params.toString() ? `?${params.toString()}` : ''

      const [pdfResponse, pptResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/pdf/public/documents${queryString}`),
        fetch(`${API_BASE_URL}/ppt/public/documents${queryString}`)
      ])

      if (!pdfResponse.ok) {
        throw new Error(`获取 PDF 公开文档失败: ${pdfResponse.status}`)
      }
      if (!pptResponse.ok) {
        throw new Error(`获取 PPT 公开文档失败: ${pptResponse.status}`)
      }

      const pdfData = await pdfResponse.json()
      const pptData = await pptResponse.json()

      const conceptDocs: any[] = []
      const regularPdfs: any[] = []

      pdfData.forEach((doc: any) => {
        if (doc.original_filename && doc.original_filename.startsWith('concept_')) {
          conceptDocs.push(doc)
        } else {
          regularPdfs.push(doc)
        }
      })

      const conceptWithType: PublicDocument[] = conceptDocs.map((doc: any) => ({
        ...doc,
        document_type: 'concept' as const,
        page_count: doc.page_count
      }))

      const pdfWithType: PublicDocument[] = regularPdfs.map((doc: any) => ({
        ...doc,
        document_type: 'pdf' as const,
        page_count: doc.page_count
      }))

      const pptWithType: PublicDocument[] = pptData.map((doc: any) => ({
        ...doc,
        document_type: 'ppt' as const,
        page_count: doc.slide_count
      }))

      const allDocuments = [...conceptWithType, ...pdfWithType, ...pptWithType].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )

      setDocuments(allDocuments)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取公开文档失败')
    } finally {
      setLoading(false)
    }
  }

  const groupDocumentsByRoot = (docs: PublicDocument[]): DocumentGroup[] => {
    const rootMap = new Map<string, DocumentGroup>()
    const childVersions: PublicDocument[] = []

    docs.forEach((doc) => {
      const rootId = doc.root_document_id ?? doc.id
      const groupKey = `${doc.document_type}:${rootId}`

      if (doc.root_document_id) {
        childVersions.push(doc)
      } else {
        rootMap.set(groupKey, {
          rootDocument: doc,
          versions: []
        })
      }
    })

    childVersions.forEach((child) => {
      const rootId = child.root_document_id!
      const groupKey = `${child.document_type}:${rootId}`

      if (rootMap.has(groupKey)) {
        rootMap.get(groupKey)!.versions.push(child)
      } else {
        rootMap.set(groupKey, {
          rootDocument: child,
          versions: []
        })
      }
    })

    rootMap.forEach((group) => {
      group.versions.sort((a, b) => (a.version_number || 0) - (b.version_number || 0))
    })

    return Array.from(rootMap.values()).sort(
      (a, b) => new Date(b.rootDocument.created_at).getTime() - new Date(a.rootDocument.created_at).getTime()
    )
  }

  const toggleVersionList = (groupKey: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev)
      if (next.has(groupKey)) {
        next.delete(groupKey)
      } else {
        next.add(groupKey)
      }
      return next
    })
  }

  useEffect(() => {
    fetchPublicDocuments()
  }, [dateFrom, dateTo])

  const filteredDocuments = useMemo(
    () => documents.filter((doc) => (documentTypeFilter === 'all' ? true : doc.document_type === documentTypeFilter)),
    [documents, documentTypeFilter]
  )

  const documentGroups = useMemo(() => groupDocumentsByRoot(filteredDocuments), [filteredDocuments])

  const completedCount = documents.filter((d) => d.status === 'ready').length
  const processingCount = documents.filter((d) => d.status === 'processing').length
  const latestDocuments = documents.slice(0, 6)

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_15%_20%,_#f6f8ff_0%,_#ebefff_35%,_#e8ebf5_65%,_#e8eaef_100%)] [font-family:'Poppins','Noto_Sans_SC','PingFang_SC','Microsoft_YaHei',sans-serif]">
      <div className="overflow-hidden rounded-none border-0 bg-white/30 shadow-none backdrop-blur-sm">
        <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[320px_minmax(0,1fr)]">
          <aside className="border-b border-slate-200/70 bg-white/78 p-5 backdrop-blur-sm lg:border-b-0 lg:border-r">
            <div className="mb-5 flex items-center px-2 py-2">
              <img src="/images/图标.jpg" alt="MAIC-UI Logo" className="mr-3 h-8 w-8 rounded-md object-cover" />
              <div className="text-[1.65rem] font-semibold tracking-tight text-slate-900">
                {t('dashboard.title')}
              </div>
            </div>

            <div className="mb-5 rounded-2xl border border-slate-200/80 bg-white/90 p-3">
              <button
                onClick={() => router.push('/dashboard')}
                className="mb-2 w-full rounded-xl px-3 py-2.5 text-left text-lg font-semibold text-slate-800 transition hover:bg-slate-50"
              >
                {t('nav.dashboard')}
              </button>
              <button
                onClick={() => router.push('/templates')}
                className="mb-2 w-full rounded-xl px-3 py-2.5 text-left text-lg font-semibold text-slate-800 transition hover:bg-slate-50"
              >
                {t('nav.templates')}
              </button>
              <button className="w-full rounded-xl bg-violet-50 px-3 py-2.5 text-left text-lg font-semibold text-violet-700">
                {t('nav.public_docs')}
              </button>
            </div>

            <div className="mb-5 grid grid-cols-3 gap-3">
              <div className="rounded-xl border border-slate-200/80 bg-white/90 p-3">
                <p className="text-xs text-slate-500">{language === 'zh' ? '总公开' : 'Total'}</p>
                <p className="mt-1 text-xl font-semibold text-slate-900">{documents.length}</p>
              </div>
              <div className="rounded-xl border border-slate-200/80 bg-white/90 p-3">
                <p className="text-xs text-slate-500">{t('dashboard.completed')}</p>
                <p className="mt-1 text-xl font-semibold text-emerald-600">{completedCount}</p>
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
                  onClick={() => document.getElementById('public-filter')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                  className="flex w-full items-center rounded-lg px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-violet-50 hover:text-violet-700"
                >
                  {language === 'zh' ? '文档筛选' : 'Filter Documents'}
                </button>
                <button
                  onClick={() => document.getElementById('public-list')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                  className="flex w-full items-center rounded-lg px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-violet-50 hover:text-violet-700"
                >
                  {language === 'zh' ? '公开文档列表' : 'Public Documents List'}
                </button>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200/80 bg-white/90 p-3">
              <p className="px-1 pb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{language === 'zh' ? '最近公开' : 'Recent Public'}</p>
              <div className="space-y-2">
                {latestDocuments.length === 0 ? (
                  <p className="px-2 py-3 text-xs text-slate-500">{language === 'zh' ? '暂无公开文档' : 'No public documents'}</p>
                ) : (
                  latestDocuments.map((doc) => {
                    const link = doc.document_type === 'ppt' ? `/ppt-viewer/${doc.id}` : `/public/document/${doc.id}`
                    return (
                      <button
                        key={`side-${doc.document_type}-${doc.id}`}
                        onClick={() => window.open(link, '_blank')}
                        className="w-full rounded-lg border border-slate-200/80 bg-white px-2.5 py-2 text-left transition hover:border-violet-300 hover:bg-violet-50/70"
                      >
                        <p className="line-clamp-1 text-sm font-medium text-slate-800">{doc.title}</p>
                        <p className="mt-0.5 text-xs text-slate-500">
                          {doc.document_type.toUpperCase()} · {new Date(doc.created_at).toLocaleDateString()}
                        </p>
                      </button>
                    )
                  })
                )}
              </div>
            </div>
          </aside>

          <main className="bg-gradient-to-b from-white/78 to-white/52 p-5 sm:p-6 lg:p-8">
            <div className="rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-[0_14px_40px_rgba(40,50,90,0.08)] sm:p-6">
              <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{language === 'zh' ? '公开文档中心' : 'Public Documents Center'}</h1>
                  <p className="mt-1 text-sm text-slate-600">{language === 'zh' ? '这里展示所有公开分享的学习资源，任何人都可以查看与学习' : 'All publicly shared learning resources, available for everyone to view and learn'}</p>
                </div>
                <div className="flex items-start gap-3">
                  {/* Language Selector */}
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setIsLanguageDropdownOpen((prev) => !prev)}
                      className="flex items-center justify-between rounded-xl border border-slate-300 bg-white px-3 py-2 text-left text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                    >
                      <span className="font-semibold">{languages.find(l => l.value === language)?.label}</span>
                      <svg className={`ml-2 h-4 w-4 transition-transform ${isLanguageDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    {isLanguageDropdownOpen && (
                      <div className="absolute right-0 z-50 mt-2 w-[100px] overflow-hidden rounded-xl border border-slate-300 bg-white shadow-lg">
                        {languages.map((lang) => (
                          <button
                            key={lang.value}
                            type="button"
                            onClick={() => { setLanguage(lang.value); setIsLanguageDropdownOpen(false) }}
                            className={`w-full px-3 py-2 text-left transition hover:bg-slate-50 ${language === lang.value ? 'bg-violet-50' : ''}`}
                          >
                            <span className="font-semibold text-slate-900">{lang.label}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  {/* User Info */}
                  <div className="rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-xs text-slate-700">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium text-slate-900">{t('dashboard.login_info')}</p>
                      {user && (
                        <button
                          onClick={handleLogout}
                          className="rounded border border-slate-300 bg-white px-2 py-0.5 text-xs text-slate-600 transition hover:bg-slate-50"
                        >
                          {t('dashboard.logout')}
                        </button>
                      )}
                    </div>
                    <p className="mt-0.5">{t('dashboard.user')}: {user?.username || (language === 'zh' ? '访客' : 'Guest')}</p>
                    <p className="text-slate-500">{user?.email || '-'}</p>
                  </div>
                </div>
              </div>

              {/* Filter Section */}
              <div id="public-filter" className="mb-6 rounded-2xl border border-slate-200 bg-white p-5">
                <h2 className="text-lg font-semibold text-slate-900">{language === 'zh' ? '筛选文档' : 'Filter Documents'}</h2>
                <div className="mt-4 space-y-4">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">{language === 'zh' ? '文档类型' : 'Document Type'}</label>
                    <div className="flex flex-wrap gap-2">
                      {[
                        { key: 'all', label: language === 'zh' ? '全部' : 'All' },
                        { key: 'pdf', label: 'PDF' },
                        { key: 'ppt', label: 'PPT' },
                        { key: 'concept', label: language === 'zh' ? '知识点' : 'Concept' }
                      ].map((item) => (
                        <button
                          key={item.key}
                          onClick={() => setDocumentTypeFilter(item.key as 'all' | 'pdf' | 'ppt' | 'concept')}
                          className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                            documentTypeFilter === item.key
                              ? 'bg-violet-600 text-white'
                              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                          }`}
                        >
                          {item.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 items-end gap-4 md:grid-cols-3">
                    <div>
                      <label htmlFor="dateFrom" className="mb-2 block text-sm font-medium text-slate-700">
                        {language === 'zh' ? '开始日期（年/月/日）' : 'Start Date (YYYY/MM/DD)'}
                      </label>
                      <input
                        id="dateFrom"
                        type="text"
                        value={dateFrom}
                        onChange={(e) => setDateFrom(e.target.value)}
                        placeholder="yyyy/mm/dd"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-200"
                      />
                    </div>

                    <div>
                      <label htmlFor="dateTo" className="mb-2 block text-sm font-medium text-slate-700">
                        {language === 'zh' ? '结束日期（年/月/日）' : 'End Date (YYYY/MM/DD)'}
                      </label>
                      <input
                        id="dateTo"
                        type="text"
                        value={dateTo}
                        onChange={(e) => setDateTo(e.target.value)}
                        placeholder="yyyy/mm/dd"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-200"
                      />
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => { setDateFrom(''); setDateTo(''); setDocumentTypeFilter('all') }}
                        className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50"
                      >
                        {language === 'zh' ? '清除筛选' : 'Clear Filters'}
                      </button>
                      <button
                        onClick={fetchPublicDocuments}
                        className="rounded-lg bg-violet-600 px-4 py-2 text-sm text-white transition hover:bg-violet-700"
                      >
                        {language === 'zh' ? '刷新' : 'Refresh'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {loading && (
                <div className="py-14 text-center text-slate-500">
                  <div className="mx-auto mb-3 h-10 w-10 animate-spin rounded-full border-2 border-violet-200 border-t-violet-600" />
                  {language === 'zh' ? '正在加载公开文档...' : 'Loading public documents...'}
                </div>
              )}

              {!loading && error && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-red-700">{error}</div>
              )}

              {!loading && !error && (
                <div id="public-list">
                  {documentGroups.length === 0 ? (
                    <div className="py-12 text-center">
                      <div className="mb-3 text-5xl">📚</div>
                      <p className="text-lg font-medium text-slate-900">{language === 'zh' ? '暂无符合条件的公开文档' : 'No public documents found'}</p>
                      <p className="mt-1 text-sm text-slate-500">{language === 'zh' ? '你可以调整筛选条件后重试' : 'Try adjusting your filters'}</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
                      {documentGroups.map((group) => {
                        const doc = group.rootDocument
                        const hasVersions = group.versions.length > 0
                        const groupKey = `${doc.document_type}:${doc.root_document_id ?? doc.id}`
                        const isExpanded = expandedGroups.has(groupKey)
                        const isPPT = doc.document_type === 'ppt'
                        const isConcept = doc.document_type === 'concept'
                        const fileTypeLabel = isConcept ? (language === 'zh' ? '知识点' : 'Concept') : isPPT ? 'PPT' : 'PDF'
                        const viewLink = isPPT ? `/ppt-viewer/${doc.id}` : `/public/document/${doc.id}`
                        const displayTitle =
                          isConcept && doc.original_filename?.startsWith('concept_')
                            ? doc.original_filename.replace('concept_', '')
                            : doc.title

                        return (
                          <div
                            key={`${doc.document_type}-${doc.id}`}
                            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"
                          >
                            <div className="mb-4 flex items-start justify-between gap-3">
                              <div className="min-w-0 flex-1">
                                <h3 className="line-clamp-2 text-lg font-semibold text-slate-900">{displayTitle}</h3>
                                {!isConcept && (
                                  <p className="mt-1 line-clamp-1 text-sm text-slate-500">{doc.original_filename}</p>
                                )}
                              </div>
                              <div className="flex flex-col gap-2">
                                <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700">{language === 'zh' ? '公开' : 'Public'}</span>
                                <span className="rounded-full bg-violet-100 px-2.5 py-0.5 text-xs font-medium text-violet-700">{fileTypeLabel}</span>
                                {hasVersions && (
                                  <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-700">
                                    {group.versions.length + 1} {language === 'zh' ? '版本' : 'versions'}
                                  </span>
                                )}
                              </div>
                            </div>

                            <div className="mb-4 space-y-1.5 text-sm text-slate-600">
                              <div className="flex justify-between">
                                <span>{isPPT ? (language === 'zh' ? '幻灯片数' : 'Slides') : (language === 'zh' ? '页数' : 'Pages')}</span>
                                <span className="font-medium text-slate-900">{doc.page_count}</span>
                              </div>
                              {doc.subject && (
                                <div className="flex justify-between">
                                  <span>{language === 'zh' ? '科目' : 'Subject'}</span>
                                  <span className="font-medium text-slate-900">{doc.subject}</span>
                                </div>
                              )}
                              {doc.grade_level && (
                                <div className="flex justify-between">
                                  <span>{language === 'zh' ? '年级' : 'Grade'}</span>
                                  <span className="font-medium text-slate-900">{doc.grade_level} {language === 'zh' ? '年级' : 'Grade'}</span>
                                </div>
                              )}
                              <div className="flex justify-between">
                                <span>{language === 'zh' ? '上传时间' : 'Upload Date'}</span>
                                <span className="font-medium text-slate-900">{new Date(doc.created_at).toLocaleDateString()}</span>
                              </div>
                            </div>

                            {doc.description && <p className="mb-4 line-clamp-3 text-sm text-slate-600">{doc.description}</p>}

                            {hasVersions && (
                              <div className="mb-4">
                                <button
                                  onClick={() => toggleVersionList(groupKey)}
                                  className="flex items-center gap-2 text-sm text-violet-600 transition hover:text-violet-800"
                                >
                                  <svg
                                    className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                  >
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                  </svg>
                                  {isExpanded ? (language === 'zh' ? '收起版本列表' : 'Collapse versions') : `${language === 'zh' ? '查看其他' : 'View other'} ${group.versions.length} ${language === 'zh' ? '个版本' : 'versions'}`}
                                </button>

                                {isExpanded && (
                                  <div className="mt-3 space-y-2 border-l-2 border-violet-200 pl-3">
                                    {group.versions.map((version) => {
                                      const versionLink = isPPT ? `/ppt-viewer/${version.id}` : `/public/document/${version.id}`
                                      return (
                                        <div
                                          key={version.id}
                                          className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2 text-sm"
                                        >
                                          <div className="flex min-w-0 items-center gap-2">
                                            <span className="font-medium text-violet-600">v{version.version_number}</span>
                                            <span className="truncate text-slate-600">{version.title}</span>
                                          </div>
                                          <Link href={versionLink} className="text-xs font-medium text-violet-600 hover:text-violet-800">
                                            {language === 'zh' ? '查看' : 'View'}
                                          </Link>
                                        </div>
                                      )
                                    })}
                                  </div>
                                )}
                              </div>
                            )}

                            <Link
                              href={viewLink}
                              className="block w-full rounded-lg bg-violet-600 px-4 py-2 text-center font-medium text-white transition hover:bg-violet-700"
                            >
                              {isPPT ? (language === 'zh' ? '查看演示文稿' : 'View Presentation') : (language === 'zh' ? '查看学习内容' : 'View Content')}
                            </Link>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
