'use client'

import React, { useEffect, useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import { WebEditor, DocumentVersion } from '@/components/WebEditor'
import { VersionList } from '@/components/VersionList'
import { useLanguage, Language } from '@/components/providers/LanguageProvider'

const API_BASE_URL =
  process.env.NODE_ENV === 'production'
    ? '/api'
    : process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

interface ConceptData {
  subject?: string
  concept_name?: string
  concept_overview?: string
  mastery_points?: string
  design_idea?: string
}

interface KnowledgeCard {
  title?: string
  summary_md?: string
}

interface KnowledgeCardsPayload {
  cards?: KnowledgeCard[]
}

interface AnalysisData {
  key_concepts?: string[]
  learning_objectives?: string[]
  prerequisite_knowledge?: string[]
  main_topics?: string[]
}

interface InteractiveElement {
  type?: string
  question?: string
  options?: string[]
  correct_answer?: number
  explanation?: string
  word?: string
  definition?: string
  description?: string
  title?: string
}

interface DocumentData {
  id: number
  title: string
  original_filename: string
  page_count: number
  subject?: string
  grade_level?: number
  description?: string
  status: 'ready' | 'processing' | 'error' | string
  website?: string
  analysis?: AnalysisData
  knowledge_cards?: KnowledgeCardsPayload
  interactive_elements?: InteractiveElement[]
  concept_data?: ConceptData
  error_message?: string
  created_at: string
}

interface PublicDocumentViewerProps {
  documentId: number
}

export function PublicDocumentViewer({ documentId }: PublicDocumentViewerProps) {
  const [document, setDocument] = useState<DocumentData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showWebsite, setShowWebsite] = useState(false)
  const [editStatus, setEditStatus] = useState<'idle' | 'processing' | 'completed'>('idle')
  const [versions, setVersions] = useState<DocumentVersion[]>([])
  const [customWebsiteHtml, setCustomWebsiteHtml] = useState('')
  const [quizAnswers, setQuizAnswers] = useState<Record<string, number>>({})
  const [showResults, setShowResults] = useState<Record<string, boolean>>({})
  const [hoveredKnowledgeIndex, setHoveredKnowledgeIndex] = useState<number | null>(null)
  const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false)

  const { language, setLanguage, t } = useLanguage()

  const languages: { value: Language; label: string }[] = [
    { value: 'zh', label: '中文' },
    { value: 'en', label: 'English' },
  ]

  const websiteIframeRef = useRef<HTMLIFrameElement | null>(null)
  const currentWebsiteVersionIdRef = useRef<number | null>(null)

  const loadCurrentVersionWebsite = async (currentVersion: DocumentVersion) => {
    const versionId = Number(currentVersion.documentId)
    if (Number.isNaN(versionId)) return
    if (currentWebsiteVersionIdRef.current === versionId && customWebsiteHtml) return

    try {
      const response = await fetch(`${API_BASE_URL}/pdf/public/documents/${versionId}`)
      if (!response.ok) throw new Error('获取当前版本内容失败')
      const data = await response.json()
      setCustomWebsiteHtml(data.website || '')
      currentWebsiteVersionIdRef.current = versionId
    } catch (err) {
      console.error('Failed to load current version website:', err)
    }
  }

  const fetchVersions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/web/public/documents/${documentId}/versions`)
      if (!response.ok) throw new Error(`获取版本失败: ${response.status}`)

      const result = await response.json()
      const backendVersions = (result.versions || []).map((version: {
        id: number
        title: string
        version_number: number
        is_current: number
        is_root: boolean
        created_at: string | null
        user_prompt: string | null
      }): DocumentVersion => ({
        id: String(version.id),
        documentId: version.id,
        versionNumber: version.version_number,
        name: version.title,
        modifiedDate: version.created_at || new Date().toISOString(),
        modificationPrompt: version.user_prompt || '无修改指令',
        html: '',
        isCurrent: Number(version.is_current) === 1,
        isRoot: Boolean(version.is_root)
      }))

      setVersions(backendVersions)

      const currentVersion = backendVersions.find((v: DocumentVersion) => v.isCurrent)
      if (currentVersion) await loadCurrentVersionWebsite(currentVersion)
    } catch (err) {
      console.error('Failed to fetch versions:', err)
    }
  }

  const fetchDocument = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/pdf/public/documents/${documentId}`)

      if (!response.ok) {
        if (response.status === 404) throw new Error('未找到公开文档')
        throw new Error(`获取文档失败: ${response.status}`)
      }

      const data: DocumentData = await response.json()
      setDocument(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取文档失败')
    } finally {
      setLoading(false)
    }
  }

  const checkEditStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/web/public/edit/${documentId}/status`)
      if (!response.ok) return
      const result = await response.json()
      if (result.status === 'processing') setEditStatus('processing')
      else if (result.status === 'ready') setEditStatus('completed')
      else if (result.status === 'error') setEditStatus('idle')
    } catch (err) {
      console.error('Failed to check edit status:', err)
    }
  }

  const checkProcessingStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/pdf/public/documents/${documentId}/processing-status`)
      if (!response.ok) return
      const status = await response.json()
      if (status.status === 'ready') fetchDocument()
    } catch {
      // ignore polling errors
    }
  }

  useEffect(() => {
    fetchDocument()
    fetchVersions()
    checkEditStatus()
  }, [documentId])

  useEffect(() => {
    if (editStatus !== 'processing') return
    const interval = setInterval(checkEditStatus, 5000)
    return () => clearInterval(interval)
  }, [editStatus, documentId])

  useEffect(() => {
    if (document?.status !== 'processing') return
    const timer = setInterval(checkProcessingStatus, 5000)
    return () => clearInterval(timer)
  }, [document?.status, documentId])

  const handleVersionSaved = () => {
    fetchVersions()
  }

  const handleApplyVersion = async (version: DocumentVersion) => {
    try {
      const response = await fetch(`${API_BASE_URL}/pdf/public/documents/${version.documentId}`)
      if (!response.ok) throw new Error('获取版本内容失败')
      const data = await response.json()

      setCustomWebsiteHtml(data.website || '')
      setDocument(data)
      setShowWebsite(false)

      const setCurrentResponse = await fetch(
        `${API_BASE_URL}/web/public/documents/${documentId}/versions/${version.documentId}/set-current`,
        { method: 'POST' }
      )
      if (!setCurrentResponse.ok) {
        const errorData = await setCurrentResponse.json().catch(() => ({ detail: '设置当前版本失败' }))
        throw new Error(errorData.detail || '设置当前版本失败')
      }

      await fetchVersions()
    } catch (err) {
      console.error('Failed to apply version:', err)
    }
  }

  const handleDeleteVersion = async (version: DocumentVersion) => {
    try {
      const versionId = Number(version.documentId)
      if (Number.isNaN(versionId)) throw new Error('无效的版本ID')
      const response = await fetch(`${API_BASE_URL}/web/public/documents/${documentId}/versions/${versionId}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('删除失败')
      await fetchVersions()
    } catch (err) {
      console.error('Failed to delete version:', err)
    }
  }

  const handleDownloadPdf = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/pdf/public/documents/${documentId}/download`)
      if (!response.ok) throw new Error('下载失败')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = window.document.createElement('a')
      a.href = url
      a.download = document?.original_filename || 'document.pdf'
      window.document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      window.document.body.removeChild(a)
    } catch {
      alert('下载失败，请稍后重试')
    }
  }

  const handleDownloadHtml = () => {
    const htmlToDownload = customWebsiteHtml || document?.website
    if (!htmlToDownload) {
      alert('该文档没有可下载的网页文件')
      return
    }

    const blob = new Blob([htmlToDownload], { type: 'text/html;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const a = window.document.createElement('a')
    a.href = url
    const baseName = (document?.title || document?.original_filename || 'document').replace(/\.pdf$/i, '')
    a.download = `${baseName}.html`
    window.document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    window.document.body.removeChild(a)
  }

  const handleQuizAnswer = (elementIndex: string, answerIndex: number) => {
    setQuizAnswers((prev) => ({ ...prev, [elementIndex]: answerIndex }))
  }

  const checkAnswer = (element: InteractiveElement, elementIndex: string) => {
    const userAnswer = quizAnswers[elementIndex]
    const isCorrect = userAnswer === element.correct_answer
    setShowResults((prev) => ({ ...prev, [elementIndex]: true }))
    return isCorrect
  }

  const resetQuiz = (elementIndex: string) => {
    setQuizAnswers((prev) => {
      const newAnswers = { ...prev }
      delete newAnswers[elementIndex]
      return newAnswers
    })
    setShowResults((prev) => {
      const newResults = { ...prev }
      delete newResults[elementIndex]
      return newResults
    })
  }

  const conceptName = useMemo(() => {
    return (
      document?.concept_data?.concept_name ||
      (Array.isArray(document?.analysis?.key_concepts) && document?.analysis?.key_concepts?.[0]) ||
      '未指定'
    )
  }, [document])

  const learningObjectives = useMemo(() => {
    return Array.isArray(document?.analysis?.learning_objectives) ? document.analysis.learning_objectives : []
  }, [document])

  const prerequisiteItems = useMemo(() => {
    if (Array.isArray(document?.analysis?.prerequisite_knowledge) && document.analysis?.prerequisite_knowledge?.length) {
      return document.analysis.prerequisite_knowledge
    }
    return (document?.knowledge_cards?.cards || []).map((card) => card.title).filter(Boolean) as string[]
  }, [document])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="h-16 w-16 animate-spin rounded-full border-2 border-violet-200 border-t-violet-600" />
          <p className="mt-4 text-lg text-slate-600">{t('public_doc.loading')}</p>
        </div>
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-red-700">{t('public_doc.error')}{error || t('public_doc.not_found')}</div>
      </div>
    )
  }

  if (showWebsite && (document.website || customWebsiteHtml)) {
    const htmlToShow = customWebsiteHtml || document.website
    return (
      <div className="relative min-h-screen bg-slate-100">
        <WebEditor
          targetIframeRef={websiteIframeRef}
          documentId={document?.id ?? documentId}
          isPublic={true}
          onEditStatusChange={setEditStatus}
          onVersionSaved={handleVersionSaved}
        />
        <button
          onClick={() => setShowWebsite(false)}
          className="fixed left-5 top-5 z-20 rounded-lg border border-slate-300 bg-white/95 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-white"
        >
          返回结果页
        </button>
        <iframe
          ref={websiteIframeRef}
          srcDoc={htmlToShow}
          className="h-screen w-full border-0"
          sandbox="allow-scripts allow-same-origin allow-forms allow-modals allow-popups"
          title="交互式学习网站"
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_15%_20%,_#f6f8ff_0%,_#ebefff_35%,_#e8ebf5_65%,_#e8eaef_100%)] [font-family:'Poppins','Noto_Sans_SC','PingFang_SC','Microsoft_YaHei',sans-serif]">
      <div className="overflow-hidden rounded-none border-0 bg-white/30 shadow-none backdrop-blur-sm">
        <div className="grid min-h-screen grid-cols-1 xl:grid-cols-[360px_minmax(0,1fr)]">
          <aside className="border-b border-slate-200/70 bg-white/78 p-5 backdrop-blur-sm xl:border-b-0 xl:border-r">
            <div className="mb-5 flex items-center justify-between px-2 py-2">
              <div className="flex items-center">
                <img src="/images/图标.jpg" alt="MAIC-UI Logo" className="mr-3 h-8 w-8 rounded-md object-cover" />
                <div className="text-[1.65rem] font-semibold tracking-tight text-slate-900">
                  MAIC-UI<span className="ml-1 text-[1.05rem]">Studio</span>
                </div>
              </div>
              {/* Language Selector */}
              <div className="relative">
                <button
                  onClick={() => setIsLanguageDropdownOpen(!isLanguageDropdownOpen)}
                  className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                >
                  <span>{languages.find(l => l.value === language)?.label}</span>
                  <svg className={`h-4 w-4 transition-transform ${isLanguageDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {isLanguageDropdownOpen && (
                  <div className="absolute right-0 z-50 mt-2 w-32 overflow-hidden rounded-lg border border-slate-300 bg-white shadow-lg">
                    {languages.map((lang) => (
                      <button
                        key={lang.value}
                        onClick={() => {
                          setLanguage(lang.value)
                          setIsLanguageDropdownOpen(false)
                        }}
                        className={`w-full px-3 py-2 text-left text-sm transition hover:bg-slate-50 ${language === lang.value ? 'bg-violet-50 font-medium text-violet-700' : 'text-slate-700'}`}
                      >
                        {lang.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-5">
              <div className="rounded-2xl border border-slate-200/80 bg-white/90 p-6 shadow-[0_12px_30px_rgba(40,50,90,0.08)]">
                <h2 className="text-[1.75rem] font-bold text-slate-900">{t('public_doc.course_info')}</h2>
                <div className="mt-4 space-y-2 text-[1.15rem] leading-relaxed text-slate-800">
                  <p>{t('public_doc.subject')}: {document.subject || document.concept_data?.subject || t('public_doc.not_specified')}</p>
                  <p>{t('public_doc.grade')}: {document.grade_level ? `${document.grade_level}${t('public_doc.grade_suffix')}` : t('public_doc.not_specified')}</p>
                  <p>{t('public_doc.knowledge_point')}: {conceptName}</p>
                  <p>{t('public_doc.pages')}: {document.page_count}</p>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200/80 bg-white/90 p-6 shadow-[0_12px_30px_rgba(40,50,90,0.08)]">
                <h2 className="text-[1.75rem] font-bold text-slate-900">{t('public_doc.teaching_content')}</h2>
                <div className="mt-4 space-y-5 text-[0.98rem] leading-7 text-slate-700">
                  {document.concept_data?.concept_overview && (
                    <div>
                      <h3 className="mb-2 text-xl font-semibold text-slate-900">{t('public_doc.concept_overview')}</h3>
                      <p className="whitespace-pre-wrap">{document.concept_data.concept_overview}</p>
                    </div>
                  )}
                  {learningObjectives.length > 0 && (
                    <div>
                      <h3 className="mb-2 text-xl font-semibold text-slate-900">{t('public_doc.learning_objectives')}</h3>
                      <ul className="list-disc space-y-1 pl-6">
                        {learningObjectives.map((objective, index) => (
                          <li key={index}>{objective}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {(document.description || document.concept_data?.design_idea) && (
                    <div>
                      <h3 className="mb-2 text-xl font-semibold text-slate-900">{t('public_doc.teaching_approach')}</h3>
                      <p className="whitespace-pre-wrap">{document.concept_data?.design_idea || document.description}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </aside>

          <main className="bg-gradient-to-b from-white/78 to-white/52 p-5 sm:p-6 lg:p-8">
            <div className="space-y-6 rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-[0_14px_40px_rgba(40,50,90,0.08)] sm:p-6">
              <div className="rounded-2xl border border-green-200/80 bg-white/95 p-6 shadow-[0_10px_28px_rgba(40,50,90,0.08)]">
                <div className="mb-5 flex flex-col items-center text-center">
                  <h1 className="text-[2.5rem] font-bold leading-tight text-slate-900">{t('public_doc.generated_complete')}</h1>
                  <p className="mt-2 text-[1.75rem] text-slate-600">{t('public_doc.new_experience')}</p>
                  <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
                    <span className="inline-flex w-fit items-center rounded-full bg-green-100 px-4 py-2 text-lg font-semibold text-green-700">
                      {t('public_doc.ready')}
                    </span>
                    {editStatus === 'processing' && (
                      <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-sm font-semibold text-amber-700">{t('public_doc.edit_processing')}</span>
                    )}
                    {editStatus === 'completed' && (
                      <span className="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-700">{t('public_doc.edit_completed')}</span>
                    )}
                  </div>
                </div>

                <div className="flex flex-wrap justify-center gap-3">
                  <button
                    onClick={() => {
                      checkEditStatus()
                      setShowWebsite(true)
                    }}
                    disabled={!(document.status === 'ready' && (document.website || customWebsiteHtml))}
                    className="rounded-xl bg-gradient-to-r from-violet-600 via-purple-500 to-fuchsia-500 px-6 py-3 text-xl font-semibold text-white shadow-[0_12px_28px_rgba(124,77,255,0.35)] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {t('public_doc.start_learning')}
                  </button>
                  <button
                    onClick={handleDownloadHtml}
                    disabled={!(document.website || customWebsiteHtml)}
                    className="rounded-xl border border-slate-300 bg-white px-5 py-3 text-xl font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {t('public_doc.download_course')}
                  </button>
                  <button
                    onClick={handleDownloadPdf}
                    className="rounded-xl border border-slate-300 bg-white px-5 py-3 text-xl font-medium text-slate-700 transition hover:bg-slate-50"
                  >
                    {t('public_doc.download_pdf')}
                  </button>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-6 shadow-[0_10px_28px_rgba(40,50,90,0.08)]">
                <h2 className="mb-4 text-[1.5rem] font-bold text-slate-900">{t('public_doc.version_section')}</h2>
                <VersionList
                  versions={versions}
                  onApplyVersion={handleApplyVersion}
                  onDeleteVersion={handleDeleteVersion}
                  className="!rounded-xl !border !border-slate-200 !shadow-none"
                  label={t('public_doc.interactive_versions')}
                />
                {versions.length === 0 && <p className="text-sm text-slate-500">{t('public_doc.no_versions')}</p>}
              </div>

              {document.website && (
                <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-6 shadow-[0_10px_28px_rgba(40,50,90,0.08)]">
                  <h2 className="text-[2.3rem] font-bold text-slate-900">{t('public_doc.preview_section')}</h2>
                  <p className="mt-2 text-lg text-slate-500">{t('public_doc.preview_desc')}</p>
                  <div className="mt-5 overflow-hidden rounded-xl border border-slate-200 bg-white">
                    <iframe
                      srcDoc={customWebsiteHtml || document.website}
                      title={t('public_doc.preview_section')}
                      className="h-[920px] w-full"
                      sandbox="allow-scripts allow-same-origin allow-forms allow-modals allow-popups"
                    />
                  </div>
                </div>
              )}

              {document.analysis && (
                <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-6 shadow-[0_10px_28px_rgba(40,50,90,0.08)]">
                  <h3 className="text-xl font-semibold text-slate-900">{t('public_doc.analysis_section')}</h3>
                  {Array.isArray(document.analysis.main_topics) && document.analysis.main_topics.length > 0 && (
                    <div className="mt-4">
                      <p className="mb-2 text-sm text-slate-500">{t('public_doc.main_topics')}</p>
                      <div className="flex flex-wrap gap-2">
                        {document.analysis.main_topics.map((topic, index) => (
                          <span key={index} className="rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800">{topic}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {prerequisiteItems.length > 0 && (
                    <div className="mt-4">
                      <p className="mb-2 text-sm text-slate-500">{t('public_doc.prerequisite')}</p>
                      <div className="flex flex-wrap gap-2">
                        {prerequisiteItems.map((item, index) => {
                          const knowledgeCards = document.knowledge_cards?.cards || []
                          const card = knowledgeCards[index] || knowledgeCards.find((entry) => entry.title === item)

                          return (
                            <div
                              key={index}
                              className="relative"
                              onMouseEnter={() => setHoveredKnowledgeIndex(index)}
                              onMouseLeave={() => setHoveredKnowledgeIndex(null)}
                            >
                              <span className="cursor-default rounded-full bg-yellow-100 px-3 py-1 text-sm text-yellow-800">{item}</span>
                              {hoveredKnowledgeIndex === index && card && (
                                <div className="absolute left-0 top-full z-20 mt-2 w-80 max-w-[18rem] rounded-lg border border-yellow-200 bg-white p-3 shadow-lg">
                                  <div className="mb-2 text-sm font-semibold text-gray-900">{card.title || item}</div>
                                  <div className="text-sm leading-relaxed text-gray-700">
                                    <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                                      {card.summary_md || ''}
                                    </ReactMarkdown>
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {Array.isArray(document.interactive_elements) && document.interactive_elements.length > 0 && (
                <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-6 shadow-[0_10px_28px_rgba(40,50,90,0.08)]">
                  <h3 className="mb-4 text-xl font-semibold text-slate-900">{t('public_doc.interactive_section')}</h3>
                  <div className="space-y-4">
                    {document.interactive_elements.map((element, index) => {
                      const elementKey = `element-${index}`
                      const hasAnswered = quizAnswers[elementKey] !== undefined
                      const showResult = showResults[elementKey]

                      if (element.type === 'quiz' && element.question && Array.isArray(element.options)) {
                        return (
                          <div key={index} className="rounded-xl border border-slate-200 p-4">
                            <p className="mb-3 font-medium text-slate-900">{element.question}</p>
                            <div className="space-y-2">
                              {element.options.map((option, optionIndex) => {
                                const isSelected = quizAnswers[elementKey] === optionIndex
                                const isCorrect = element.correct_answer === optionIndex
                                const showCorrect = showResult && isCorrect
                                const showIncorrect = showResult && isSelected && !isCorrect

                                return (
                                  <button
                                    key={optionIndex}
                                    onClick={() => !showResult && handleQuizAnswer(elementKey, optionIndex)}
                                    disabled={showResult}
                                    className={`w-full rounded-lg border-2 p-3 text-left transition ${
                                      showCorrect
                                        ? 'border-green-500 bg-green-50'
                                        : showIncorrect
                                          ? 'border-red-500 bg-red-50'
                                          : isSelected
                                            ? 'border-blue-500 bg-blue-50'
                                            : 'border-slate-200 bg-white hover:border-slate-300'
                                    }`}
                                  >
                                    {String.fromCharCode(65 + optionIndex)}. {option}
                                  </button>
                                )
                              })}
                            </div>

                            <div className="mt-3 flex gap-2">
                              {!showResult && hasAnswered && (
                                <button
                                  onClick={() => checkAnswer(element, elementKey)}
                                  className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
                                >
                                  {t('public_doc.check_answer')}
                                </button>
                              )}
                              {showResult && (
                                <button
                                  onClick={() => resetQuiz(elementKey)}
                                  className="rounded-md bg-slate-600 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
                                >
                                  {t('public_doc.try_again')}
                                </button>
                              )}
                            </div>
                          </div>
                        )
                      }

                      return (
                        <div key={index} className="rounded-xl border border-slate-200 p-4 text-slate-700">
                          {element.title || element.word || element.question || element.description || (language === 'zh' ? '交互元素' : 'Interactive Element')}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {document.status === 'processing' && (
                <div className="rounded-2xl border border-blue-200 bg-blue-50 p-6">
                  <div className="flex items-center gap-3">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-200 border-t-blue-600" />
                    <div>
                      <h3 className="text-xl font-medium text-blue-900">{t('public_doc.processing_doc')}</h3>
                      <p className="text-blue-700">{t('public_doc.processing_desc')}</p>
                    </div>
                  </div>
                </div>
              )}

              {document.status === 'error' && (
                <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
                  <h3 className="mb-1 text-xl font-medium text-red-900">{t('public_doc.process_failed')}</h3>
                  <p className="text-red-700">{document.error_message || t('public_doc.unknown_error')}</p>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}