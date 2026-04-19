'use client';

import { useRouter, useParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import Cookies from 'js-cookie';

const API_BASE_URL = process.env.NODE_ENV === 'production' ? '/api' : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api');

interface DocumentInfo {
  id: number;
  title: string;
  original_filename: string;
  file_type: string;
  slide_count?: number;
  status: string;
}

interface SlideThumbnail {
  page_number: number;
  thumbnail: string | null;
  selected: boolean;
}

interface ThumbnailsResponse {
  document_id: number;
  title: string;
  file_type: string;
  slide_count: number;
  thumbnails: SlideThumbnail[];
}

// Time estimation constants
const MINUTES_PER_PAGE = 5; // 5 minutes per page for specific pages mode
const MINUTES_PER_DEMO = 5; // 5 minutes per demo
const AVG_DEMOS_PER_BATCH = 2; // Average 2 demos per batch

/**
 * Calculate estimated processing time based on mode and configuration
 * @param mode Processing mode ('batch' or 'specific_pages')
 * @param batchSize Batch size for batch mode
 * @param totalPages Total number of pages in document
 * @param selectedPages Selected page numbers for specific_pages mode
 * @returns Estimated time in minutes
 */
function calculateEstimatedTime(
  mode: 'batch' | 'specific_pages',
  batchSize: number,
  totalPages: number,
  selectedPages: number[]
): number {
  if (mode === 'specific_pages') {
    // For specific pages: selected_pages * 5 minutes
    return selectedPages.length * MINUTES_PER_PAGE;
  } else {
    // For batch mode: (total_pages / batch_size) * 2 * 5
    const numberOfBatches = Math.ceil(totalPages / batchSize);
    return numberOfBatches * AVG_DEMOS_PER_BATCH * MINUTES_PER_DEMO;
  }
}

/**
 * Format estimated time into human-readable string
 * @param minutes Time in minutes
 * @returns Formatted string like "需要 15 分钟"
 */
function formatEstimatedTime(minutes: number, mode: 'batch' | 'specific_pages', batchSize: number, totalPages: number, selectedPagesCount: number): string {
  if (mode === 'specific_pages') {
    return `需要 ${selectedPagesCount} * ${MINUTES_PER_PAGE} = ${minutes} 分钟`;
  } else {
    const numberOfBatches = Math.ceil(totalPages / batchSize);
    return `需要 ${totalPages} / ${batchSize} * ${AVG_DEMOS_PER_BATCH} * ${MINUTES_PER_DEMO} = ${minutes} 分钟`;
  }
}

export default function PPTConfigPage() {
  const router = useRouter();
  const params = useParams();
  const documentId = parseInt(params.documentId as string);

  const [document, setDocument] = useState<DocumentInfo | null>(null);
  const [thumbnails, setThumbnails] = useState<SlideThumbnail[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingThumbnails, setLoadingThumbnails] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Processing mode
  const [mode, setMode] = useState<'batch' | 'specific_pages'>('specific_pages');
  const [batchSize, setBatchSize] = useState(5);
  const [selectAll, setSelectAll] = useState(false);
  const [useTemplates, setUseTemplates] = useState(false);

  const getAuthToken = () => {
    return Cookies.get('access_token');
  };

  useEffect(() => {
    fetchDocumentInfo();
  }, [documentId]);

  const fetchDocumentInfo = async () => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error('需要身份验证');
      }

      const response = await fetch(`${API_BASE_URL}/ppt/documents/${documentId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`获取文档信息失败：${response.status}`);
      }

      const data: DocumentInfo = await response.json();
      setDocument(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取文档信息失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (mode === 'specific_pages' && thumbnails.length === 0) {
      fetchThumbnails();
    }
  }, [mode]);

  const fetchThumbnails = async () => {
    try {
      setLoadingThumbnails(true);
      const token = getAuthToken();
      if (!token) {
        throw new Error('需要身份验证');
      }

      const response = await fetch(`${API_BASE_URL}/ppt/documents/${documentId}/thumbnails`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`获取幻灯片预览失败：${response.status}`);
      }

      const data: ThumbnailsResponse = await response.json();
      setThumbnails(data.thumbnails);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取幻灯片预览失败');
    } finally {
      setLoadingThumbnails(false);
    }
  };

  const toggleSlideSelection = (pageNumber: number) => {
    setThumbnails(prev =>
      prev.map(slide =>
        slide.page_number === pageNumber
          ? { ...slide, selected: !slide.selected }
          : slide
      )
    );
  };

  const toggleSelectAll = () => {
    const newValue = !selectAll;
    setSelectAll(newValue);
    setThumbnails(prev => prev.map(slide => ({ ...slide, selected: newValue })));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error('需要身份验证');
      }

      const formData = new FormData();
      formData.append('mode', mode);
      formData.append('use_templates', useTemplates.toString());

      if (mode === 'batch') {
        formData.append('batch_size', batchSize.toString());
      } else {
        // Get selected page numbers from thumbnails
        const selectedPages = thumbnails
          .filter(slide => slide.selected)
          .map(slide => slide.page_number);

        if (selectedPages.length === 0) {
          throw new Error('请至少选择一个页面');
        }

        formData.append('selected_pages', JSON.stringify(selectedPages));
      }

      const response = await fetch(`${API_BASE_URL}/ppt/documents/${documentId}/configure`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `配置失败：${response.status}`);
      }

      const result = await response.json();

      // Show success message and redirect
      alert(result.message || '处理已开始！');
      router.push(`/ppt-viewer/${documentId}`);

    } catch (err) {
      setError(err instanceof Error ? err.message : '配置失败');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">正在加载文档信息...</p>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">文档未找到</p>
          <button
            onClick={() => router.push('/ppt-upload')}
            className="text-indigo-600 hover:text-indigo-800"
          >
            返回上传页面
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            配置PPT分析选项
          </h1>
          <p className="text-gray-600 mb-4">
            文档：{document.title}
          </p>
          <div className="text-sm text-gray-500">
            <p>文件名：{document.original_filename}</p>
            <p>类型：{document.file_type?.toUpperCase()}</p>
            {document.slide_count && (
              <p>总页数：{document.slide_count} 页</p>
            )}
          </div>
        </div>

        {/* Configuration Form */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            选择处理模式
          </h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Mode Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                处理模式
              </label>
              <div className="space-y-2">
                <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="mode"
                    value="batch"
                    checked={mode === 'batch'}
                    onChange={(e) => setMode(e.target.value as 'batch')}
                    className="mr-3"
                  />
                  <div>
                    <span className="font-medium text-gray-900">批量处理</span>
                    <p className="text-sm text-gray-500">
                      AI将按照设定的批次大小自动分析所有页面，AI会自主决定给哪些页面生成交互演示
                    </p>
                  </div>
                </label>

                <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="mode"
                    value="specific_pages"
                    checked={mode === 'specific_pages'}
                    onChange={(e) => setMode(e.target.value as 'specific_pages')}
                    className="mr-3"
                  />
                  <div>
                    <span className="font-medium text-gray-900">指定页面</span>
                    <p className="text-sm text-gray-500">
                      您可以选择性地为特定页面生成交互式演示（实验模拟、流程展示等）
                    </p>
                  </div>
                </label>
              </div>
            </div>

            {/* Batch Size Input (for batch mode) */}
            {mode === 'batch' && (
              <div>
                <label htmlFor="batch_size" className="block text-sm font-medium text-gray-700 mb-2">
                  批次大小
                </label>
                <input
                  type="number"
                  id="batch_size"
                  value={batchSize}
                  onChange={(e) => setBatchSize(parseInt(e.target.value) || 5)}
                  min={1}
                  max={20}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                <p className="text-sm text-gray-500 mt-1">
                  每批次分析的页面数（1-20）。较大的批次可以提高速度，但可能增加API成本。
                </p>
              </div>
            )}

            {/* Template Workflow Option */}
            <div className="border-t pt-6">
              <label className="block text-sm font-medium text-gray-700 mb-3">
                演示生成方式
              </label>
              <div className="space-y-2">
                <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="use_templates"
                    value="true"
                    checked={useTemplates === true}
                    onChange={() => setUseTemplates(true)}
                    className="mr-3"
                  />
                  <div>
                    <span className="font-medium text-gray-900">使用模板库 </span>
                    <p className="text-sm text-gray-500">
                      从模板库中选择合适的模板生成演示。系统会根据内容推荐最佳匹配的模板，您也可以手动选择。生成的演示质量更高。
                    </p>
                  </div>
                </label>

                <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="use_templates"
                    value="false"
                    checked={useTemplates === false}
                    onChange={() => setUseTemplates(false)}
                    className="mr-3"
                  />
                  <div>
                    <span className="font-medium text-gray-900">AI 直接生成</span>
                    <p className="text-sm text-gray-500">
                      不使用模板，由AI从头开始生成交互式演示。这种方式速度更快。
                    </p>
                  </div>
                </label>
              </div>
              {useTemplates && (
                <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm text-green-800">
                    ✓ 优点：质量更稳定、可直接预览模板效果
                  </p>
                </div>
              )}
            </div>

            {/* Slide Thumbnails (for specific_pages mode) */}
            {mode === 'specific_pages' && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <label className="block text-sm font-medium text-gray-700">
                    选择要分析的页面
                  </label>
                  <button
                    type="button"
                    onClick={toggleSelectAll}
                    className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                  >
                    {selectAll ? '取消全选' : '全选'}
                  </button>
                </div>

                {loadingThumbnails ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">正在加载幻灯片预览...</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                    {thumbnails.map((slide) => (
                      <div
                        key={slide.page_number}
                        className={`relative cursor-pointer border-2 rounded-lg overflow-hidden transition-all ${
                          slide.selected
                            ? 'border-indigo-600 ring-2 ring-indigo-300'
                            : 'border-gray-300 hover:border-indigo-400'
                        }`}
                        onClick={() => toggleSlideSelection(slide.page_number)}
                      >
                        {/* Checkbox overlay */}
                        <div className="absolute top-2 left-2 z-10">
                          <div className={`w-6 h-6 rounded border-2 flex items-center justify-center ${
                            slide.selected
                              ? 'bg-indigo-600 border-indigo-600'
                              : 'bg-white border-gray-400'
                          }`}>
                            {slide.selected && (
                              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            )}
                          </div>
                        </div>

                        {/* Slide thumbnail */}
                        {slide.thumbnail ? (
                          <img
                            src={slide.thumbnail}
                            alt={`Page ${slide.page_number}`}
                            className="w-full h-auto"
                          />
                        ) : (
                          <div className="aspect-video bg-gray-200 flex items-center justify-center">
                            <span className="text-gray-500 text-sm">Page {slide.page_number}</span>
                          </div>
                        )}

                        {/* Page number label */}
                        <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 text-white text-xs py-1 text-center">
                          第 {slide.page_number} 页
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Selection summary */}
                {!loadingThumbnails && thumbnails.length > 0 && (
                  <div className="mt-4 p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
                    <p className="text-sm text-indigo-800">
                      已选择 <span className="font-bold">{thumbnails.filter(t => t.selected).length}</span> 页，
                      共 <span className="font-bold">{thumbnails.length}</span> 页
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-medium text-blue-900 mb-2">处理说明</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• AI将分析您选择的页面，识别需要交互式演示的概念</li>
                <li>• 处理过程可能需要几分钟时间</li>
                <li>• 完成后您可以查看包含演示的交互式幻灯片</li>
              </ul>
            </div>

            {/* Time Estimation */}
            {document.slide_count && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="font-medium text-yellow-900 mb-2">⏱️ 预计处理时间</h3>
                <div className="text-sm text-yellow-800">
                  <p className="font-semibold mb-1">
                    {mode === 'specific_pages'
                      ? formatEstimatedTime(
                          calculateEstimatedTime(mode, batchSize, document.slide_count, thumbnails.filter(t => t.selected).map(t => t.page_number)),
                          mode,
                          batchSize,
                          document.slide_count,
                          thumbnails.filter(t => t.selected).length
                        )
                      : formatEstimatedTime(
                          calculateEstimatedTime(mode, batchSize, document.slide_count, []),
                          mode,
                          batchSize,
                          document.slide_count,
                          0
                        )
                    }
                  </p>
                  <p className="text-xs text-yellow-700 mt-2">
                    {mode === 'specific_pages'
                      ? `基于已选择的 ${thumbnails.filter(t => t.selected).length} 页，每页约需 ${MINUTES_PER_PAGE} 分钟处理`
                      : `基于总共 ${document.slide_count} 页，批次大小 ${batchSize}，平均每批次 ${AVG_DEMOS_PER_BATCH} 个演示，每个演示约需 ${MINUTES_PER_DEMO} 分钟`
                    }
                  </p>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => router.push('/ppt-upload')}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={submitting || (mode === 'specific_pages' && thumbnails.filter(t => t.selected).length === 0)}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {submitting ? '正在开始处理...' : '开始处理'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
