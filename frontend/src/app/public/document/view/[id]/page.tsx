'use client'

import React, { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'

const API_BASE_URL = process.env.NODE_ENV === 'production' ? '/api' : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api')

interface DocumentViewData {
  id: number
  title: string
  website: string
}

export default function PublicDocumentViewPage() {
  const params = useParams()
  const documentId = parseInt(params.id as string)

  const [data, setData] = useState<DocumentViewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isNaN(documentId)) {
      setError('无效的文档 ID')
      setLoading(false)
      return
    }

    const fetchDocumentView = async () => {
      try {
        // Use existing public document endpoint (returns 'website' field)
        const response = await fetch(`${API_BASE_URL}/pdf/public/documents/${documentId}`)
        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || 'Failed to fetch document')
        }
        const result = await response.json()
        setData(result)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load document')
      } finally {
        setLoading(false)
      }
    }

    fetchDocumentView()
  }, [documentId])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          错误：{error}
        </div>
      </div>
    )
  }

  if (!data || !data.website) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          错误：未找到文档内容
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <iframe
        srcDoc={data.website}
        style={{
          width: '100%',
          height: '100vh',
          border: 'none',
          display: 'block'
        }}
        sandbox="allow-scripts allow-same-origin allow-forms allow-modals allow-popups"
      />
    </div>
  )
}
