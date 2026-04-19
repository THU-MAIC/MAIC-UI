'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { previewTemplate } from '../../../../services/templateApi';


export default function TemplatePreviewPage() {
  const params = useParams();
  const router = useRouter();
  const templateId = params.templateId as string;

  const [html, setHtml] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const previewIframeRef = useRef<HTMLIFrameElement | null>(null);

  useEffect(() => {
    const loadPreview = async () => {
      try {
        setLoading(true);
        setError(null);

        const result = await previewTemplate(templateId);
        setHtml(result.html);
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载预览失败');
      } finally {
        setLoading(false);
      }
    };

    if (templateId) {
      loadPreview();
    }
  }, [templateId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <svg
            className="animate-spin h-12 w-12 text-indigo-600 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          <p className="text-gray-600">正在加载模板预览...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md">
          <svg
            className="h-12 w-12 text-red-600 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900 mb-2 text-center">加载失败</h3>
          <p className="text-gray-600 text-center mb-4">{error}</p>
          <button
            onClick={() => window.close()}
            className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            关闭
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">模板预览</h1>
          <p className="text-sm text-gray-500">模板ID: {templateId}</p>
        </div>
        <button
          onClick={() => window.close()}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
        >
          关闭
        </button>
      </div>

      {/* Preview Frame */}
      <div className="flex-1 bg-gray-100">
        <iframe
          srcDoc={html}
          ref={previewIframeRef}
          className="w-full h-full border-0"
          title="Template Preview"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>
    </div>
  );
}
