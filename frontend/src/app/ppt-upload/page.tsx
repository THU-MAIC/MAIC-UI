'use client';

import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import PPTUploadForm from '@/components/ppt-viewer/PPTUploadForm';
import Navigation from '@/components/Navigation';
import { useAuth } from '@/components/providers/AuthProvider';
import { QRCodeHover } from '@/components/QRCodeHover';
import Cookies from 'js-cookie';
const API_BASE_URL = process.env.NODE_ENV === 'production' ? '/api' : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api');

interface PPTDocument {
  id: number;
  title: string;
  original_filename: string;
  file_type: string;
  slide_count?: number;
  subject?: string;
  grade_level?: number;
  status: string;
  created_at: string;
  updated_at: string;
  root_document_id?: number | null;
  version_number?: number;
  is_current?: number;
}

interface DocumentGroup {
  rootDocument: PPTDocument;
  versions: PPTDocument[];
}

export default function PPTUploadPage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [documents, setDocuments] = useState<PPTDocument[]>([]);
  const [deletingIds, setDeletingIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const getAuthToken = () => {
    return Cookies.get('access_token');
  };

  const fetchDocuments = async () => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error('需要身份验证');
      }

      const response = await fetch(API_BASE_URL + '/ppt/documents?limit=100', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`获取文档失败：${response.status}`);
      }

      const data: PPTDocument[] = await response.json();
      setDocuments(data);
      setError(null);

    } catch (err) {
      setError(err instanceof Error ? err.message : '获取文档失败');
    } finally {
      setLoading(false);
    }
  };

  // Group documents by root_document_id (same pattern as public_documents)
  const groupDocumentsByRoot = (docs: PPTDocument[]): DocumentGroup[] => {
    const rootMap = new Map<string, DocumentGroup>();
    const childVersions: PPTDocument[] = [];

    // First pass: identify root documents and child versions
    docs.forEach(doc => {
      const rootId = doc.root_document_id ?? doc.id;
      const groupKey = String(rootId);

      // A document is a child if it has root_document_id AND it's different from its own id
      // (handles both null root_document_id and self-referential root_document_id)
      const isChild = doc.root_document_id != null && doc.root_document_id !== doc.id;

      if (isChild) {
        // This is a child version
        childVersions.push(doc);
      } else {
        // This is a root document (or standalone document without versioning)
        rootMap.set(groupKey, {
          rootDocument: doc,
          versions: []
        });
      }
    });

    // Second pass: assign child versions to their root groups
    childVersions.forEach(child => {
      const rootId = child.root_document_id!;
      const groupKey = String(rootId);

      if (rootMap.has(groupKey)) {
        rootMap.get(groupKey)!.versions.push(child);
      } else {
        // Root document might not be in the list, check if there's an existing group
        const existingGroup = Array.from(rootMap.values()).find(
          g => g.rootDocument.id === rootId || g.versions.some(v => v.root_document_id === rootId)
        );
        if (!existingGroup) {
          // Create a group with this child as the "root" for display purposes
          rootMap.set(groupKey, {
            rootDocument: child,  // Use child as representative
            versions: []
          });
        } else {
          existingGroup.versions.push(child);
        }
      }
    });

    // Sort versions within each group by version_number ascending
    rootMap.forEach(group => {
      group.versions.sort((a, b) => (a.version_number || 0) - (b.version_number || 0));
    });

    // Convert to array and sort by root document's created_at (newest first)
    return Array.from(rootMap.values()).sort((a, b) =>
      new Date(b.rootDocument.created_at).getTime() - new Date(a.rootDocument.created_at).getTime()
    );
  };

  const handleDeleteDocument = async (documentId: number, title: string) => {
    const token = getAuthToken();
    if (!token) {
      setError('需要身份验证');
      return;
    }

    const confirmed = window.confirm(`确认删除文档「${title}」吗？\n这会删除该文档及其所有版本。`);
    if (!confirmed) {
      return;
    }

    setDeletingIds((prev) => [...prev, documentId]);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/ppt/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`删除文档失败：${response.status}`);
      }

      const result = await response.json();
      const deletedIds: number[] = Array.isArray(result.deleted_document_ids)
        ? result.deleted_document_ids
        : [documentId];

      setDocuments((prev) => prev.filter((doc) => !deletedIds.includes(doc.id)));
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除文档失败');
    } finally {
      setDeletingIds((prev) => prev.filter((id) => id !== documentId));
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  return (
    <div className="min-h-screen bg-gray-100">
      <Navigation user={user || undefined} onLogout={handleLogout} />

      {/* QR Code Hover Component */}
      <QRCodeHover position="right" top="50%" />

      <div className="max-w-4xl mx-auto py-12 px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            将演示文稿转换为互动学习体验
          </h1>
          <p className="text-lg text-gray-600">
            上传您的PPT或PDF文件，AI将自动生成交互式演示，帮助学生理解复杂概念
          </p>
        </div>

        {/* Upload Form */}
        <PPTUploadForm
          onSuccess={(documentId) => {
            fetchDocuments(); // Refresh the list after successful upload
            router.push(`/ppt-viewer/${documentId}`);
          }}
        />

        {/* My PPT Documents Section */}
        <div className="bg-white rounded-lg shadow-lg p-6 mt-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900">
              我的PPT文档
            </h2>
            <button
              onClick={fetchDocuments}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '刷新中...' : '刷新'}
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-4">
              错误：{error}
            </div>
          )}

          {loading && documents.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              <span className="ml-3 text-gray-600">正在加载文档...</span>
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">您还没有上传任何PPT文档。</p>
              <p className="text-sm text-gray-400">请上传PPT或PDF文件以开始使用！</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {groupDocumentsByRoot(documents).map((group) => {
                const doc = group.rootDocument;

                return (
                  <div
                    key={doc.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
<div className="flex justify-between items-start gap-2 mb-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-900 truncate leading-snug">
                          {doc.title}
                        </h3>
                        {doc.original_filename && (
                          <p className="text-sm text-gray-600 truncate">{doc.original_filename}</p>
                        )}
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium flex-shrink-0 self-start
                        ${doc.status === 'ready' ? 'bg-green-100 text-green-800' :
                          doc.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'}`}>
                        {doc.status === 'ready' ? '就绪' :
                         doc.status === 'processing' ? '处理中...' :
                         '错误'}
                      </span>
                    </div>

                    <div className="text-sm text-gray-600 space-y-1">
                      <p className="truncate">
                        <span className="font-medium">类型：</span> {doc.file_type?.toUpperCase()}
                      </p>
                      {doc.slide_count && (
                        <p>
                          <span className="font-medium">幻灯片数：</span> {doc.slide_count}
                        </p>
                      )}
                      {doc.subject && (
                        <p>
                          <span className="font-medium">科目：</span> {doc.subject}
                        </p>
                      )}
                      {doc.grade_level && (
                        <p>
                          <span className="font-medium">年级：</span> {doc.grade_level}
                        </p>
                      )}
                      <p>
                        <span className="font-medium">上传时间：</span> {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-gray-100 flex flex-col gap-2">
                      <button
                        className="w-full px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={deletingIds.includes(doc.id)}
                        onClick={() => window.open(`/ppt-viewer/${doc.id}`, '_blank')}
                      >
                        {doc.status === 'ready' ? '查看演示文稿' :
                         doc.status === 'processing' ? '检查状态' :
                         '查看详情'}
                      </button>

                      <button
                        className="w-full px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 border border-red-200 rounded-md hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={deletingIds.includes(doc.id)}
                        onClick={() => handleDeleteDocument(doc.id, doc.title)}
                      >
                        {deletingIds.includes(doc.id) ? '删除中...' : '删除文档'}
                      </button>
                    </div>

                    {doc.status === 'processing' && (
                      <div className="mt-2 text-xs text-yellow-600 text-center">
                        处理可能需要几分钟时间...
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Features */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg p-6 shadow-md">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">支持PPT和PDF</h3>
            <p className="text-gray-600 text-sm">上传PowerPoint演示文稿或PDF文件进行自动处理</p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-md">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">AI智能分析</h3>
            <p className="text-gray-600 text-sm">我们的AI会识别哪些概念最需要交互式演示来帮助理解</p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-md">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">交互式演示</h3>
            <p className="text-gray-600 text-sm">自动生成的模拟、可视化和练习练习，让学习更生动</p>
          </div>
        </div>

        {/* Back Button */}
        <div className="mt-8 text-center">
          <button
            onClick={() => router.push('/dashboard')}
            className="text-indigo-600 hover:text-indigo-800 font-medium"
          >
            ← 返回仪表盘
          </button>
        </div>
      </div>
    </div>
  );
}
