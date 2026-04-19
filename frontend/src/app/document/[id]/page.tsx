'use client'

import React from 'react'
import { useParams } from 'next/navigation'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { DocumentViewer } from '@/components/pdf/DocumentViewer'
import { useLanguage } from '@/components/providers/LanguageProvider'

function DocumentPageContent() {
  const params = useParams()
  const { t } = useLanguage()
  const documentId = parseInt(params.id as string)

  if (isNaN(documentId)) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {t('public_doc.invalid_id')}
        </div>
      </div>
    )
  }

  return <DocumentViewer documentId={documentId} />
}

export default function DocumentPage() {
  return (
    <ProtectedRoute>
      <DocumentPageContent />
    </ProtectedRoute>
  )
}
