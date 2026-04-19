'use client'

import React from 'react'
import { useParams } from 'next/navigation'
import { PublicDocumentViewer } from '@/components/pdf/PublicDocumentViewer'

export default function PublicDocumentPage() {
  const params = useParams()
  const documentId = parseInt(params.id as string)

  if (isNaN(documentId)) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          无效的文档ID
        </div>
      </div>
    )
  }

  return <PublicDocumentViewer documentId={documentId} />
}