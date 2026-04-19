'use client'

import React, { useState } from 'react'
import Cookies from 'js-cookie'
import { Button } from '@/components/ui/Button'
import { useModelSettings } from '@/components/providers/ModelSettingsProvider'
import { useLanguage } from '@/components/providers/LanguageProvider'

const API_BASE_URL =
  process.env.NODE_ENV === 'production'
    ? '/api'
    : process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

interface UploadResponse {
  id: number
  title: string
  status: string
}

interface ConceptFormData {
  subject: string
  concept_name: string
  concept_overview: string
  mastery_points: string
  design_idea: string
  grade_level: string
  description: string
  interests: string
}

export function ConceptInputForm() {
  const { selectedModel } = useModelSettings()
  const { t, language } = useLanguage()
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [formData, setFormData] = useState<ConceptFormData>({
    subject: '',
    concept_name: '',
    concept_overview: '',
    mastery_points: '',
    design_idea: '',
    grade_level: '',
    description: '',
    interests: ''
  })

  const [autoNavigate, setAutoNavigate] = useState(true)
  const [isPublic, setIsPublic] = useState(false)
  const [includeExercises, setIncludeExercises] = useState(false)
  const [includePrerequisites, setIncludePrerequisites] = useState(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const getAuthToken = () => Cookies.get('access_token')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    if (!formData.subject.trim()) return setError(t('concept.error_subject'))
    if (!formData.concept_name.trim()) return setError(t('concept.error_name'))
    if (!formData.concept_overview.trim()) return setError(t('concept.error_overview'))
    if (!formData.mastery_points.trim()) return setError(t('concept.error_mastery'))
    if (!formData.design_idea.trim()) return setError(t('concept.error_design'))

    setUploading(true)
    try {
const formDataToSend = new FormData()
      formDataToSend.append('subject', formData.subject)
      formDataToSend.append('concept_name', formData.concept_name)
      formDataToSend.append('concept_overview', formData.concept_overview)
      formDataToSend.append('mastery_points', formData.mastery_points)
      formDataToSend.append('design_idea', formData.design_idea)

      // Only send grade_level if it's not empty
      if (formData.grade_level && formData.grade_level !== '') {
        formDataToSend.append('grade_level', parseInt(formData.grade_level).toString())
      }

      formDataToSend.append('description', formData.description.trim())
      formDataToSend.append('is_public', String(isPublic))
      formDataToSend.append('interests', formData.interests.trim())
      formDataToSend.append('include_exercises', String(includeExercises))
      formDataToSend.append('include_prerequisites', String(includePrerequisites))
      formDataToSend.append('ai_model', selectedModel)
      formDataToSend.append('language', language)  // Pass the current language preference

      const token = getAuthToken()
      if (!token) throw new Error(t('upload.error_login_submit'))

      const response = await fetch(`${API_BASE_URL}/pdf/concept/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formDataToSend
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.message || `${t('upload.submit_failed')}${response.status}`)
      }

      const result: UploadResponse = await response.json()
      setSuccess(`${t('concept.submit_success')}”${result.title}” ${t('upload.upload_success')}`)

      if (autoNavigate) {
        setTimeout(() => window.open(`/document/${result.id}`, '_blank'), 1200)
      }

      setFormData({
        subject: '',
        concept_name: '',
        concept_overview: '',
        mastery_points: '',
        design_idea: '',
        grade_level: '',
        description: '',
        interests: ''
      })
      setIsPublic(false)
      setIncludeExercises(false)
      setIncludePrerequisites(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('upload.error_submit_failed'))
    } finally {
      setUploading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <p className="mb-3 text-[16px] font-semibold text-slate-900">{t('upload.basic_settings')}</p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="subject" className="mb-1 block text-[13px] font-medium text-slate-700">
              {t('concept.subject')}
            </label>
            <input
              id="subject"
              name="subject"
              value={formData.subject}
              onChange={handleInputChange}
              required
              disabled={uploading}
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-[#7C4DFF] focus:ring-2 focus:ring-[#7C4DFF]/20"
              placeholder={t('concept.subject_placeholder')}
            />
          </div>
          <div>
            <label htmlFor="concept_name" className="mb-1 block text-[13px] font-medium text-slate-700">
              {t('concept.name')}
            </label>
            <input
              id="concept_name"
              name="concept_name"
              value={formData.concept_name}
              onChange={handleInputChange}
              required
              disabled={uploading}
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-[#7C4DFF] focus:ring-2 focus:ring-[#7C4DFF]/20"
              placeholder={t('concept.name_placeholder')}
            />
          </div>
          <div className="md:col-span-2">
            <label htmlFor="concept_overview" className="mb-1 block text-[13px] font-medium text-slate-700">
              {t('concept.overview')}
            </label>
            <textarea
              id="concept_overview"
              name="concept_overview"
              value={formData.concept_overview}
              onChange={handleInputChange}
              required
              disabled={uploading}
              rows={3}
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-[#7C4DFF] focus:ring-2 focus:ring-[#7C4DFF]/20"
              placeholder={t('concept.overview_placeholder')}
            />
          </div>
          <div className="md:col-span-2">
            <label htmlFor="mastery_points" className="mb-1 block text-[13px] font-medium text-slate-700">
              {t('concept.mastery_points')}
            </label>
            <textarea
              id="mastery_points"
              name="mastery_points"
              value={formData.mastery_points}
              onChange={handleInputChange}
              required
              disabled={uploading}
              rows={3}
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-[#7C4DFF] focus:ring-2 focus:ring-[#7C4DFF]/20"
              placeholder={t('concept.mastery_points_placeholder')}
            />
          </div>
          <div className="md:col-span-2">
            <label htmlFor="design_idea" className="mb-1 block text-[13px] font-medium text-slate-700">
              {t('concept.design_idea')}
            </label>
            <textarea
              id="design_idea"
              name="design_idea"
              value={formData.design_idea}
              onChange={handleInputChange}
              required
              disabled={uploading}
              rows={4}
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-[#7C4DFF] focus:ring-2 focus:ring-[#7C4DFF]/20"
              placeholder={t('concept.design_idea_placeholder')}
            />
          </div>
        </div>
      </div>

      <details className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <summary className="cursor-pointer list-none text-[16px] font-semibold text-slate-900">{t('upload.advanced_settings')}</summary>
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="grade_level" className="mb-1 block text-[13px] font-medium text-slate-700">
              {t('concept.grade')}
            </label>
            <select
              id="grade_level"
              name="grade_level"
              value={formData.grade_level}
              onChange={handleSelectChange}
              disabled={uploading}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-[#7C4DFF] focus:ring-2 focus:ring-[#7C4DFF]/20"
            >
              <option value="">{t('upload.select_grade')}</option>
              <option value="0">{t('grade.kindergarten')}</option>
              <option value="1">{t('grade.grade1')}</option>
              <option value="2">{t('grade.grade2')}</option>
              <option value="3">{t('grade.grade3')}</option>
              <option value="4">{t('grade.grade4')}</option>
              <option value="5">{t('grade.grade5')}</option>
              <option value="6">{t('grade.grade6')}</option>
              <option value="7">{t('grade.grade7')}</option>
              <option value="8">{t('grade.grade8')}</option>
              <option value="9">{t('grade.grade9')}</option>
              <option value="10">{t('grade.grade10')}</option>
              <option value="11">{t('grade.grade11')}</option>
              <option value="12">{t('grade.grade12')}</option>
              <option value="13">{t('grade.college')}</option>
              <option value="14">{t('grade.graduate')}</option>
            </select>
          </div>

          <div>
            <label htmlFor="interests" className="mb-1 block text-[13px] font-medium text-slate-700">
              {t('concept.interests')}
            </label>
            <input
              id="interests"
              name="interests"
              value={formData.interests}
              onChange={handleInputChange}
              disabled={uploading}
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-[#7C4DFF] focus:ring-2 focus:ring-[#7C4DFF]/20"
              placeholder={t('concept.interests_placeholder')}
            />
          </div>

          <div className="md:col-span-2">
            <label htmlFor="description" className="mb-1 block text-[13px] font-medium text-slate-700">
              {t('concept.custom_needs')}
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              disabled={uploading}
              rows={3}
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-[#7C4DFF] focus:ring-2 focus:ring-[#7C4DFF]/20"
              placeholder={t('concept.custom_needs_placeholder')}
            />
          </div>

          <div className="md:col-span-2 grid grid-cols-1 gap-2 md:grid-cols-2">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                disabled={uploading}
                className="h-4 w-4 rounded border-slate-300 text-[#7C4DFF] focus:ring-[#7C4DFF]"
              />
              {t('upload.make_public')}
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={autoNavigate}
                onChange={(e) => setAutoNavigate(e.target.checked)}
                disabled={uploading}
                className="h-4 w-4 rounded border-slate-300 text-[#7C4DFF] focus:ring-[#7C4DFF]"
              />
              {t('upload.auto_open')}
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={includeExercises}
                onChange={(e) => setIncludeExercises(e.target.checked)}
                disabled={uploading}
                className="h-4 w-4 rounded border-slate-300 text-[#7C4DFF] focus:ring-[#7C4DFF]"
              />
              {t('upload.include_exercises')}
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={includePrerequisites}
                onChange={(e) => setIncludePrerequisites(e.target.checked)}
                disabled={uploading}
                className="h-4 w-4 rounded border-slate-300 text-[#7C4DFF] focus:ring-[#7C4DFF]"
              />
              {t('upload.include_prerequisites')}
            </label>
          </div>
        </div>
      </details>

      {error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
      {success && <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{success}</div>}

      <div className="sticky bottom-0 z-10 rounded-2xl border border-slate-200 bg-white/90 p-3 shadow-[0_-8px_20px_rgba(15,23,42,0.08)] backdrop-blur">
        <Button
          type="submit"
          disabled={uploading}
          className="h-12 w-full rounded-xl bg-gradient-to-r from-[#7C4DFF] to-[#A855F7] text-base font-semibold text-white shadow-[0_12px_26px_rgba(124,77,255,0.3)] hover:from-[#6d3ff0] hover:to-[#9333ea]"
        >
          {uploading ? t('upload.generating') : t('upload.generate_button')}
        </Button>
      </div>

      <div className="rounded-lg border border-violet-200 bg-violet-50 p-4">
        <p className="text-sm text-violet-800">
          <strong>{t('upload.tip')}</strong>
          {t('upload.tip_desc')}
        </p>
      </div>
    </form>
  )
}

