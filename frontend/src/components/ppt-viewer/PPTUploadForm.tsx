'use client'

import React, { useCallback, useRef, useState } from 'react'
import Cookies from 'js-cookie'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/Button'
import { useModelSettings } from '@/components/providers/ModelSettingsProvider'
import { useLanguage } from '@/components/providers/LanguageProvider'

const API_BASE_URL =
  process.env.NODE_ENV === 'production'
    ? '/api'
    : process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

interface PPTUploadFormProps {
  onSuccess?: (documentId: number) => void
  embedded?: boolean
}

interface UploadResponse {
  id: number
  original_filename: string
  status: string
}

export default function PPTUploadForm({ onSuccess, embedded = false }: PPTUploadFormProps) {
  const router = useRouter()
  const { selectedModel } = useModelSettings()
  const { t } = useLanguage()
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [subject, setSubject] = useState('')
  const [gradeLevel, setGradeLevel] = useState('')
  const [description, setDescription] = useState('')
  const [isPublic, setIsPublic] = useState(false)
  const [configureProcessing, setConfigureProcessing] = useState(true)

  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const getAuthToken = () => Cookies.get('access_token')

  const applySelectedFile = useCallback((selectedFile: File) => {
    const extension = selectedFile.name.split('.').pop()?.toLowerCase()
    if (!extension || (extension !== 'pdf' && extension !== 'pptx')) {
      setError(t('upload.error_pdf_pptx_only'))
      return
    }

    setFile(selectedFile)
    setError(null)
    if (!title.trim()) {
      setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''))
    }
  }, [title, t])

  const handleDrag = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    if (e.type === 'dragleave') setDragActive(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    const dropped = e.dataTransfer.files?.[0]
    if (dropped) applySelectedFile(dropped)
  }, [applySelectedFile])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected) applySelectedFile(selected)
  }

  const resetForm = () => {
    setFile(null)
    setTitle('')
    setSubject('')
    setGradeLevel('')
    setDescription('')
    setIsPublic(false)
    setConfigureProcessing(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    if (!file) {
      setError(t('upload.error_select_first'))
      return
    }
    if (!title.trim()) {
      setError(t('upload.error_fill_title_ppt'))
      return
    }

    try {
      setUploading(true)

      const token = getAuthToken()
      if (!token) {
        router.push('/login')
        return
      }

      const extension = file.name.split('.').pop()?.toLowerCase()
      const fileType = extension === 'pptx' ? 'pptx' : 'pdf'

const formDataToSend = new FormData()
      formDataToSend.append('file', file)
      formDataToSend.append('title', title.trim())
      formDataToSend.append('file_type', fileType)
      if (subject.trim()) formDataToSend.append('subject', subject.trim())
      if (gradeLevel) formDataToSend.append('grade_level', gradeLevel)
      if (description.trim()) formDataToSend.append('description', description.trim())
      formDataToSend.append('is_public', String(isPublic))
      formDataToSend.append('auto_process', String(!configureProcessing))
      formDataToSend.append('ai_model', selectedModel)

      const response = await fetch(`${API_BASE_URL}/ppt/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formDataToSend
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.message || `${t('upload.upload_failed')}${response.status}`)
      }

      const result: UploadResponse = await response.json()
      setSuccess(`${t('upload.upload_success')}${result.original_filename}`)

      if (configureProcessing) {
        setTimeout(() => {
          if (embedded) {
            window.open(`/ppt-upload/config/${result.id}`, '_blank')
          } else {
            router.push(`/ppt-upload/config/${result.id}`)
          }
        }, 1000)
      } else if (onSuccess) {
        onSuccess(result.id)
      } else {
        setTimeout(() => {
          if (embedded) {
            window.open(`/ppt-viewer/${result.id}`, '_blank')
          } else {
            router.push(`/ppt-viewer/${result.id}`)
          }
        }, 1000)
      }

      resetForm()
    } catch (err) {
      setError(err instanceof Error ? err.message : t('upload.error_upload_failed'))
    } finally {
      setUploading(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={embedded ? 'space-y-6' : 'mx-auto max-w-4xl space-y-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm'}
    >
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <p className="mb-3 text-[16px] font-semibold text-slate-900">{t('upload.upload_file')}</p>
        <div
          className={`relative rounded-2xl border-2 border-dashed p-8 text-center transition ${
            dragActive
              ? 'border-[#7C4DFF] bg-[#f5f0ff]'
              : file
                ? 'border-emerald-300 bg-emerald-50'
                : 'border-slate-300 bg-slate-50 hover:border-slate-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.pptx"
            onChange={handleFileChange}
            className="hidden"
            disabled={uploading}
          />

          <div className="space-y-2">
            <p className="text-4xl">⬆</p>
            <p className="text-base font-semibold text-slate-800">{t('upload.drag_or_click')}</p>
            <p className="text-[13px] text-slate-500">{t('upload.support_pdf_pptx')}</p>
            <p className="pt-2 text-[13px] text-slate-500">{t('upload.example_pptx')}</p>
          </div>

          <div className="mt-5 flex items-center justify-center">
            <Button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="rounded-xl bg-[#7C4DFF] px-4 py-2 text-sm text-white hover:bg-[#6d3ff0]"
            >
              {t('upload.select_file')}
            </Button>
          </div>
        </div>

        {file && (
          <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-emerald-700">{file.name}</p>
                <p className="text-xs text-emerald-600">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  className="rounded-lg px-3 py-1.5 text-xs"
                >
                  {t('upload.replace')}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setFile(null)}
                  className="rounded-lg px-3 py-1.5 text-xs"
                >
                  {t('upload.delete')}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <p className="mb-3 text-[16px] font-semibold text-slate-900">{t('upload.basic_settings')}</p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="md:col-span-3">
            <label htmlFor="ppt_title" className="mb-1 block text-[13px] font-medium text-slate-700">
              {t('upload.title')}
            </label>
            <input
              id="ppt_title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              disabled={uploading}
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-[#7C4DFF] focus:ring-2 focus:ring-[#7C4DFF]/20"
              placeholder={t('upload.title_placeholder_ppt')}
            />
          </div>

          <div>
            <label htmlFor="ppt_grade" className="mb-1 block text-[13px] font-medium text-slate-700">
              {t('upload.grade')}
            </label>
            <select
              id="ppt_grade"
              value={gradeLevel}
              onChange={(e) => setGradeLevel(e.target.value)}
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
            </select>
          </div>

          <div className="md:col-span-2">
            <label htmlFor="ppt_subject" className="mb-1 block text-[13px] font-medium text-slate-700">
              {t('upload.subject')}
            </label>
            <input
              id="ppt_subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              disabled={uploading}
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-[#7C4DFF] focus:ring-2 focus:ring-[#7C4DFF]/20"
              placeholder={t('upload.subject_placeholder_ppt')}
            />
          </div>
        </div>
      </div>

      <details className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <summary className="cursor-pointer list-none text-[16px] font-semibold text-slate-900">{t('upload.advanced_settings')}</summary>
        <div className="mt-4 space-y-4">
          <div>
            <label htmlFor="ppt_desc" className="mb-1 block text-[13px] font-medium text-slate-700">
              {t('upload.description')}
            </label>
            <textarea
              id="ppt_desc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={uploading}
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-[#7C4DFF] focus:ring-2 focus:ring-[#7C4DFF]/20"
              placeholder={t('upload.description_placeholder_ppt')}
            />
          </div>

          <div className="grid grid-cols-1 gap-2">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                disabled={uploading}
                className="h-4 w-4 rounded border-slate-300 text-[#7C4DFF] focus:ring-[#7C4DFF]"
              />
              {t('upload.make_public_ppt')}
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={configureProcessing}
                onChange={(e) => setConfigureProcessing(e.target.checked)}
                disabled={uploading}
                className="h-4 w-4 rounded border-slate-300 text-[#7C4DFF] focus:ring-[#7C4DFF]"
              />
              {t('upload.configure_options')}
            </label>
          </div>
        </div>
      </details>

      {error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
      {success && <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{success}</div>}

      <div className="sticky bottom-0 z-10 rounded-2xl border border-slate-200 bg-white/90 p-3 shadow-[0_-8px_20px_rgba(15,23,42,0.08)] backdrop-blur">
        <Button
          type="submit"
          disabled={uploading || !file}
          className="h-12 w-full rounded-xl bg-gradient-to-r from-[#7C4DFF] to-[#A855F7] text-base font-semibold text-white shadow-[0_12px_26px_rgba(124,77,255,0.3)] hover:from-[#6d3ff0] hover:to-[#9333ea]"
        >
          {uploading ? t('upload.processing') : t('upload.generate_button')}
        </Button>
      </div>

      <div className="rounded-lg border border-violet-200 bg-violet-50 p-4">
        <p className="text-sm text-violet-800">
          <strong>{t('upload.next_steps')}</strong>
          {t('upload.next_steps_desc')}
        </p>
      </div>
    </form>
  )
}

