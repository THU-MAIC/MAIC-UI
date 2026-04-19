'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { WebEditor, DocumentVersion } from '@/components/WebEditor';
import { VersionList } from '@/components/VersionList';


const API_BASE_URL = process.env.NODE_ENV === 'production' ? '/api' : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api');

interface SlideItem {
  type: 'slide';
  slide_number: number;
  image_path: string;
  title: string;
  description: string;
}

interface DemoItem {
  type: 'demo';
  slide_number: number;
  html: string;
  reason: string;
  demo_type: string;
}

interface HTMLSlideItem {
  type: 'html_slide';
  slide_number: number;
  html: string;
  title: string;
  description: string;
}

type InteractiveItem = SlideItem | DemoItem | HTMLSlideItem;

interface InteractiveViewData {
  document_id: number;
  title: string;
  subject: string;
  grade_level: number;
  is_public?: boolean;
  total_items: number;
  items: InteractiveItem[];
}

interface StatusData {
  document_id: number;
  status: string;
  progress: number;
  message: string;
  slide_count: number;
  is_public?: boolean;
  processing_config?: {
    mode?: 'batch' | 'specific_pages';
    batch_size?: number;
    selected_pages?: number[];
  };
  template_options?: Record<number, any[]>;
}

// Time estimation constants (same as config page)
const MINUTES_PER_PAGE = 5;
const MINUTES_PER_DEMO = 5;
const AVG_DEMOS_PER_BATCH = 2;

/**
 * Calculate estimated processing time based on mode and configuration
 */
function calculateEstimatedTime(
  slide_count: number,
  processingConfig?: StatusData['processing_config']
): number {
  if (!processingConfig) {
    // Default: assume batch mode with batch_size=5
    const numberOfBatches = Math.ceil(slide_count / 5);
    return numberOfBatches * AVG_DEMOS_PER_BATCH * MINUTES_PER_DEMO;
  }

  const mode = processingConfig.mode || 'batch';

  if (mode === 'specific_pages') {
    const selectedPages = processingConfig.selected_pages || [];
    return selectedPages.length * MINUTES_PER_PAGE;
  } else {
    const batchSize = processingConfig.batch_size || 5;
    const numberOfBatches = Math.ceil(slide_count / batchSize);
    return numberOfBatches * AVG_DEMOS_PER_BATCH * MINUTES_PER_DEMO;
  }
}

/**
 * Format estimated time into human-readable string
 */
function formatEstimatedTime(minutes: number, slide_count: number, processingConfig?: StatusData['processing_config']): string {
  if (!processingConfig) {
    const numberOfBatches = Math.ceil(slide_count / 5);
    return `预计需要 ${numberOfBatches} * ${AVG_DEMOS_PER_BATCH} * ${MINUTES_PER_DEMO} = ${minutes} 分钟`;
  }

  const mode = processingConfig.mode || 'batch';

  if (mode === 'specific_pages') {
    const selectedPages = processingConfig.selected_pages || [];
    return `预计需要 ${selectedPages.length} * ${MINUTES_PER_PAGE} = ${minutes} 分钟`;
  } else {
    const batchSize = processingConfig.batch_size || 5;
    const numberOfBatches = Math.ceil(slide_count / batchSize);
    return `预计需要 ${slide_count} / ${batchSize} * ${AVG_DEMOS_PER_BATCH} * ${MINUTES_PER_DEMO} = ${minutes} 分钟`;
  }
}

// Standard PPT slide dimensions (16:9 aspect ratio)
const PPT_WIDTH = 1280;
const PPT_HEIGHT = 720;

export default function PPTViewerPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params.id as string;

  const [viewData, setViewData] = useState<InteractiveViewData | null>(null);
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNavbar, setShowNavbar] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [editStatus, setEditStatus] = useState<'idle' | 'processing' | 'completed'>('idle');
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [currentVersionId, setCurrentVersionId] = useState<number | null>(null);
  const [showVersionList, setShowVersionList] = useState(false);
  const [isDocumentPublic, setIsDocumentPublic] = useState<boolean | null>(null);
  const [lockedIndex, setLockedIndex] = useState<number | null>(null);
  const editStatusRef = useRef<'idle' | 'processing' | 'completed'>('idle');
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const demoIframeRef = useRef<HTMLIFrameElement | null>(null);
  const dragIndexRef = useRef<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [uploadingHTML, setUploadingHTML] = useState(false);

  const navLockKey = `ppt-edit-nav-lock-${documentId}`;
  const isNavigationLocked = lockedIndex !== null;

  useEffect(() => {
    checkStatusAndFetch();
    fetchVersions();

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [documentId]);

  // Restore navigation lock (editing page) after refresh/back
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const stored = window.localStorage.getItem(navLockKey);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed && typeof parsed.index === 'number') {
          setLockedIndex(parsed.index);
          setCurrentIndex(parsed.index);
        }
      } catch (err) {
        console.error('Failed to parse nav lock:', err);
        window.localStorage.removeItem(navLockKey);
      }
    }
  }, [navLockKey]);

  // Persist/clear navigation lock based on edit status changes
  useEffect(() => {
    const previousStatus = editStatusRef.current;
    const isEditingActive = editStatus === 'processing' || editStatus === 'completed';

    if (isEditingActive && lockedIndex === null) {
      setLockedIndex(currentIndex);
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(navLockKey, JSON.stringify({ index: currentIndex }));
      }
    }

    if (editStatus === 'idle' && previousStatus !== 'idle') {
      setLockedIndex(null);
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(navLockKey);
      }
    }

    editStatusRef.current = editStatus;
  }, [editStatus, currentIndex, lockedIndex, navLockKey]);

  // Ensure locked page is focused once data is available
  useEffect(() => {
    if (lockedIndex !== null && viewData) {
      const safeIndex = Math.min(Math.max(0, lockedIndex), viewData.total_items - 1);
      if (safeIndex !== currentIndex) {
        setCurrentIndex(safeIndex);
      }
    }
  }, [lockedIndex, viewData, currentIndex]);

  const fetchVersions = async () => {
    try {
      const token = Cookies.get('access_token');
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const publicResponse = await fetch(
        `${API_BASE_URL}/ppt/public/documents/${documentId}/versions`,
        { headers }
      );

      if (!publicResponse.ok && token) {
        const authResponse = await fetch(
          `${API_BASE_URL}/ppt/documents/${documentId}/versions`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }
        );

        if (!authResponse.ok) {
          throw new Error(`获取版本失败：${authResponse.status}`);
        }

        const authResult = await authResponse.json();
        const authVersions = (authResult.versions || []).map((version: {
          id: number;
          title: string;
          version_number: number;
          is_current: number;
          is_root: boolean;
          description: string | null;
          created_at: string | null;
          user_prompt: string | null;
        }): DocumentVersion => ({
          id: String(version.id),
          documentId: version.id,
          versionNumber: version.version_number,
          name: version.title,
          modifiedDate: version.created_at || new Date().toISOString(),
          modificationPrompt: version.user_prompt || version.description || '无修改指令',
          html: '',
          isCurrent: Number(version.is_current) === 1,
          isRoot: Boolean(version.is_root)
        }));

        setVersions(authVersions);
        const current = authVersions.find((v: { isCurrent: any; }) => v.isCurrent) || authVersions[0];
        setCurrentVersionId(current ? Number(current.id) : Number(documentId));
        return;
      }

      if (!publicResponse.ok) {
        throw new Error(`获取版本失败：${publicResponse.status}`);
      }

      const result = await publicResponse.json();
      const backendVersions = (result.versions || []).map((version: {
        id: number;
        title: string;
        version_number: number;
        is_current: number;
        is_root: boolean;
        description: string | null;
        created_at: string | null;
        user_prompt: string | null;
      }): DocumentVersion => ({
        id: String(version.id),
        documentId: version.id,
        versionNumber: version.version_number,
        name: version.title,
        modifiedDate: version.created_at || new Date().toISOString(),
        modificationPrompt: version.user_prompt || version.description || '无修改指令',
        html: '',
        isCurrent: Number(version.is_current) === 1,
        isRoot: Boolean(version.is_root)
      }));

      setVersions(backendVersions);
      const current = backendVersions.find((v: { isCurrent: any; }) => v.isCurrent) || backendVersions[0];
      setCurrentVersionId(current ? Number(current.id) : Number(documentId));
    } catch (err) {
      console.error('Failed to fetch versions:', err);
    }
  };

  const handleApplyVersion = async (version: DocumentVersion) => {
    try {
      const token = Cookies.get('access_token');
      const publicResponse = await fetch(
        `${API_BASE_URL}/ppt/public/documents/${documentId}/versions/${version.documentId}/set-current`,
        { method: 'POST' }
      );

      if (!publicResponse.ok && token) {
        const authResponse = await fetch(
          `${API_BASE_URL}/ppt/documents/${documentId}/versions/${version.documentId}/set-current`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }
        );

        if (!authResponse.ok) {
          const errorData = await authResponse.json().catch(() => ({ detail: '设置当前版本失败' }));
          throw new Error(errorData.detail || '设置当前版本失败');
        }
      } else if (!publicResponse.ok) {
        const errorData = await publicResponse.json().catch(() => ({ detail: '设置当前版本失败' }));
        throw new Error(errorData.detail || '设置当前版本失败');
      }

      await fetchVersions();
      await fetchInteractiveView();
      setCurrentVersionId(Number(version.documentId));
      setShowVersionList(false);
      // Unlock navigation after user selects a version post-edit
      setEditStatus('idle');
    } catch (err) {
      console.error('Failed to apply version:', err);
    }
  };

  const handleDeleteVersion = async (version: DocumentVersion) => {
    try {
      const versionId = Number(version.documentId);
      if (Number.isNaN(versionId)) {
        throw new Error('无效的版本ID');
      }

      const token = Cookies.get('access_token');
      const publicResponse = await fetch(
        `${API_BASE_URL}/ppt/public/documents/${documentId}/versions/${versionId}`,
        { method: 'DELETE' }
      );

      if (!publicResponse.ok && token) {
        const authResponse = await fetch(
          `${API_BASE_URL}/ppt/documents/${documentId}/versions/${versionId}`,
          {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }
        );

        if (!authResponse.ok) {
          const errorData = await authResponse.json().catch(() => ({ detail: '删除失败' }));
          throw new Error(errorData.detail || '删除失败');
        }
      } else if (!publicResponse.ok) {
        const errorData = await publicResponse.json().catch(() => ({ detail: '删除失败' }));
        throw new Error(errorData.detail || '删除失败');
      }

      await fetchVersions();
    } catch (err) {
      console.error('Failed to delete version:', err);
    }
  };

  // Handle Escape key to exit fullscreen
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
      }
    };

    if (isFullscreen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isFullscreen]);

  const checkStatusAndFetch = async () => {
    try {
      // Only set loading on initial load, not during polling
      if (!pollingRef.current) {
        setLoading(true);
      }
      const token = Cookies.get('access_token');

      // Try public endpoint first, then authenticated endpoint
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // First check status (try public endpoint)
      const statusResponse = await fetch(
        `${API_BASE_URL}/ppt/public/documents/${documentId}/status`,
        {
          headers: headers,
        }
      );

      // If public fails and we have a token, try authenticated endpoint
      if (!statusResponse.ok && token) {
        const authStatusResponse = await fetch(
          `${API_BASE_URL}/ppt/documents/${documentId}/status`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }
        );

        if (!authStatusResponse.ok) {
          throw new Error('Failed to fetch document status');
        }

        const status: StatusData = await authStatusResponse.json();
        if (typeof status.is_public === 'boolean') {
          setIsDocumentPublic(status.is_public);
        }
        setStatusData(status);

        if (status.status === 'ready') {
          setProcessing(false);
          await fetchInteractiveView();
        } else if (status.status === 'processing') {
          setProcessing(true);
          // Only set up polling if not already polling
          if (!pollingRef.current) {
            pollingRef.current = setInterval(checkStatusAndFetch, 2000);
          }
        } else if (status.status === 'awaiting_template_selection') {
          // Redirect to template selection page
          setProcessing(false);
          router.push(`/ppt-upload/templates/${documentId}`);
          return;
        } else {
          setProcessing(false);
          setError(status.message || 'Processing failed');
        }
        return;
      }

      if (!statusResponse.ok) {
        throw new Error('Failed to fetch document status');
      }

      const status: StatusData = await statusResponse.json();
      if (typeof status.is_public === 'boolean') {
        setIsDocumentPublic(status.is_public);
      }
      setStatusData(status);

      if (status.status === 'ready') {
        setProcessing(false);
        await fetchInteractiveView();
      } else if (status.status === 'processing') {
        setProcessing(true);
        // Only set up polling if not already polling
        if (!pollingRef.current) {
          pollingRef.current = setInterval(checkStatusAndFetch, 2000);
        }
      } else if (status.status === 'awaiting_template_selection') {
        // Redirect to template selection page
        setProcessing(false);
        router.push(`/ppt-upload/templates/${documentId}`);
        return;
      } else {
        setProcessing(false);
        setError(status.message || 'Processing failed');
      }
    } catch (err) {
      // Clear polling on error
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      setError(err instanceof Error ? err.message : '加载演示文稿失败');
      setProcessing(false);
    } finally {
      setLoading(false);
    }
  };

  const fetchInteractiveView = async () => {
    try {
      // Clear polling first - this is important to prevent continued polling
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }

      const token = Cookies.get('access_token');
      const authHeaders = token ? { 'Authorization': `Bearer ${token}` } : undefined;

      if (token) {
        const authResponse = await fetch(
          `${API_BASE_URL}/ppt/documents/${documentId}/interactive-view`,
          { headers: authHeaders }
        );

        if (authResponse.ok) {
          const data = await authResponse.json();
          setViewData(data);
          if (typeof data.is_public === 'boolean') {
            setIsDocumentPublic(data.is_public);
          }
          return;
        }
      }

      const publicResponse = await fetch(
        `${API_BASE_URL}/ppt/public/documents/${documentId}/interactive-view`
      );

      if (!publicResponse.ok) {
        const errorData = await publicResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch presentation');
      }

      const data = await publicResponse.json();
      setViewData(data);
      if (typeof data.is_public === 'boolean') {
        setIsDocumentPublic(data.is_public);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载演示文稿失败');
    }
  };

  const handleHTMLUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadingHTML(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name.replace('.html', ''));
      formData.append('insert_after_index', currentIndex.toString());

      const token = Cookies.get('access_token');
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      let response = await fetch(
        `${API_BASE_URL}/ppt/documents/${documentId}/upload-html`,
        {
          method: 'POST',
          headers,
          body: formData
        }
      );

      if (!response.ok && (!token || response.status === 401 || response.status === 403)) {
        response = await fetch(
          `${API_BASE_URL}/ppt/public/documents/${documentId}/upload-html`,
          {
            method: 'POST',
            body: formData
          }
        );
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '上传失败' }));
        throw new Error(errorData.detail || '上传失败');
      }

      const result = await response.json();
      await fetchInteractiveView();

      // After inserting HTML, navigate to the newly inserted slide
      // The slide is inserted after currentIndex, so we go to currentIndex + 1
      if (result.slide_number && viewData) {
        // The new slide should be at currentIndex + 1 (inserted after current position)
        const newIndex = currentIndex + 1;
        // Make sure we don't go out of bounds
        if (newIndex < viewData.total_items) {
          setCurrentIndex(newIndex);
        }
      }

      alert('HTML文件上传成功！');
    } catch (err) {
      alert(err instanceof Error ? err.message : '上传HTML文件失败');
    } finally {
      setUploadingHTML(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const goToPrevious = () => {
    if (isNavigationLocked) return;
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const goToNext = () => {
    if (isNavigationLocked) return;
    if (viewData && currentIndex < viewData.total_items - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const getItemKey = (item: InteractiveItem) => `${item.type}-${item.slide_number}`;

  const saveInteractiveOrder = async (items: InteractiveItem[]) => {
    try {
      const targetDocumentId = currentVersionId ?? Number(documentId);
      const token = Cookies.get('access_token');

      const payload = {
        order: items.map(item => ({
          type: item.type,
          slide_number: item.slide_number
        }))
      };

      // Try authenticated endpoint first, fall back to public endpoint
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Try authenticated endpoint first
      let response = await fetch(
        `${API_BASE_URL}/ppt/documents/${targetDocumentId}/interactive-order`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify(payload)
        }
      );

      // If auth fails or no token, try public endpoint
      if (!response.ok && (response.status === 401 || response.status === 403 || !token)) {
        response = await fetch(
          `${API_BASE_URL}/ppt/public/documents/${targetDocumentId}/interactive-order`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
          }
        );
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '保存顺序失败' }));
        console.error('Failed to save interactive order:', errorData.detail || response.status);
      }
    } catch (err) {
      console.error('Failed to save interactive order:', err);
    }
  };

  const handleDragStart = (index: number) => {
    if (isNavigationLocked) return;
    dragIndexRef.current = index;
  };

  const handleDragEnd = () => {
    dragIndexRef.current = null;
    setDragOverIndex(null);
  };

  const handleDrop = (index: number) => {
    if (isNavigationLocked) return;
    const fromIndex = dragIndexRef.current;
    if (fromIndex === null || fromIndex === index || !viewData) return;

    setViewData(prev => {
      if (!prev) return prev;

      const newItems = [...prev.items];
      const [moved] = newItems.splice(fromIndex, 1);
      newItems.splice(index, 0, moved);

      const currentItem = prev.items[currentIndex];
      const currentKey = currentItem ? getItemKey(currentItem) : null;
      if (currentKey) {
        const newIndex = newItems.findIndex(item => getItemKey(item) === currentKey);
        if (newIndex !== -1 && newIndex !== currentIndex) {
          setCurrentIndex(newIndex);
        }
      }

      saveInteractiveOrder(newItems);

      return {
        ...prev,
        items: newItems,
        total_items: newItems.length
      };
    });

    dragIndexRef.current = null;
    setDragOverIndex(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Ignore navigation keys when typing in the editor input area
    const target = e.target as HTMLElement | null
    if (target && (target.closest('#editor-mode-input') || target.closest('.editor-mode-panel'))) {
      return
    }

    if (isNavigationLocked) {
      if (['ArrowLeft', 'ArrowUp', 'ArrowRight', 'ArrowDown'].includes(e.key)) {
        e.preventDefault();
      }
      return;
    }
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      goToPrevious();
    } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      goToNext();
    }
  };

  const getCurrentItem = (): InteractiveItem | null => {
    if (!viewData || !viewData.items) return null;
    return viewData.items[currentIndex];
  };

  const jumpToPage = (index: number) => {
    if (isNavigationLocked) return;
    setCurrentIndex(index);
    // setShowNavbar(false);
  };

  const zoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 10, 200));
  };

  const zoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 10, 50));
  };

  const resetZoom = () => {
    setZoomLevel(100);
  };

  // Calculate scale to fit PPT dimensions in viewport
  const calculateFitToScreen = () => {
    if (typeof window === 'undefined') return 100;

    const maxWidth = window.innerWidth - (showNavbar ? 320 + 64 : 64); // Account for sidebar and padding
    const maxHeight = window.innerHeight - 300; // Account for header, controls, and padding

    const scaleX = (maxWidth / PPT_WIDTH) * 100;
    const scaleY = (maxHeight / PPT_HEIGHT) * 100;

    return Math.min(scaleX, scaleY, 100); // Never scale up beyond 100% for fit
  };

  const fitToScreen = () => {
    setZoomLevel(calculateFitToScreen());
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">正在加载演示文稿...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <p className="text-red-600 text-xl mb-4">{error}</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  if (processing) {
    // Calculate estimated time
    const estimatedMinutes = statusData?.slide_count
      ? calculateEstimatedTime(statusData.slide_count, statusData.processing_config)
      : null;

    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center max-w-md">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">正在处理演示文稿...</h2>
          <p className="text-gray-600 mb-4">
            {statusData?.message || 'AI 正在分析幻灯片并生成交互式演示'}
          </p>
          {statusData && (
            <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
              <div
                className="bg-indigo-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${statusData.progress}%` }}
              ></div>
            </div>
          )}
          {/* Time Estimation */}
          {estimatedMinutes && statusData?.slide_count && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm font-semibold text-yellow-900">
                ⏱️ {formatEstimatedTime(estimatedMinutes, statusData.slide_count, statusData.processing_config)}
              </p>
              <p className="text-xs text-yellow-700 mt-1">
                {statusData.processing_config?.mode === 'specific_pages'
                  ? `基于 ${statusData.processing_config.selected_pages?.length || 0} 个选定页面`
                  : `基于总共 ${statusData.slide_count} 页，批次大小 ${statusData.processing_config?.batch_size || 5}`
                }
              </p>
            </div>
          )}
          <p className="text-sm text-gray-500 mt-3">
            这可能需要几分钟时间，请勿关闭此页面
          </p>
        </div>
      </div>
    );
  }

  if (!viewData) {
    return null;
  }

  const currentItem = getCurrentItem();
  const isSlide = currentItem?.type === 'slide';
  const isDemo = currentItem?.type === 'demo';
  const isHTMLSlide = currentItem?.type === 'html_slide';
  const activeDocumentId = currentVersionId ?? Number(documentId);
  const backPath = isDocumentPublic ? '/public_documents' : '/dashboard';

  return (
    <div
      className="min-h-screen bg-gray-100 ppt-viewer-frame"
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      {isDemo && !Number.isNaN(activeDocumentId) && (
        <WebEditor
          targetIframeRef={demoIframeRef}
          documentId={activeDocumentId}
          isPublic={isDocumentPublic ?? false}
          resourceType="ppt"
          slideNumber={currentItem?.type === 'demo' ? currentItem.slide_number : undefined}
          onEditStatusChange={setEditStatus}
          onVersionSaved={async () => {
            await fetchVersions();
            await fetchInteractiveView();
          }}
          onEditModeChange={(isEditMode) => {
            if (isEditMode && editStatus === 'idle') {
              resetZoom();
            }
            if (isEditMode) {
              setShowNavbar(false);
            }
          }}
        />
      )}
      {/* Header */}
      <header className="bg-white shadow-sm border-b ppt-viewer-header">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="relative">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">{viewData.title}</h1>
              <button
                onClick={() => setShowVersionList((prev) => !prev)}
                className="px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 text-sm font-semibold shadow-sm"
                type="button"
              >
                版本管理
              </button>
            </div>
            <p className="text-sm text-gray-500">
              {viewData.subject} • {viewData.grade_level}年级
            </p>
            {showVersionList && (
              <div className="absolute left-0 mt-3 w-[calc(100vw-2rem)] max-w-7xl z-20">
                <VersionList
                  versions={versions}
                  onApplyVersion={handleApplyVersion}
                  onDeleteVersion={handleDeleteVersion}
                />
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {editStatus === 'processing' && (
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800 animate-pulse">
                编辑应用中
              </span>
            )}
            {editStatus === 'completed' && (
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                编辑已完成！
              </span>
            )}
            <button
              onClick={() => setShowNavbar(!showNavbar)}
              className="px-4 py-2 text-sm font-semibold rounded-lg border border-indigo-600 text-indigo-600 hover:bg-indigo-50 transition-colors"
            >
              {showNavbar ? '隐藏导航' : '显示导航'}
            </button>
            <button
              onClick={() => router.push(backPath)}
              className="px-4 py-2 text-sm font-semibold rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-colors"
            >
              ← 返回
            </button>
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="bg-gray-200 h-1">
        <div
          className="bg-indigo-600 h-1 transition-all duration-300"
          style={{
            width: `${((currentIndex + 1) / viewData.total_items) * 100}%`,
          }}
        ></div>
      </div>

      {/* Navigation Sidebar */}
      <div
        className={`fixed left-0 top-0 h-full w-80 bg-white shadow-2xl overflow-y-auto z-50 border-r ppt-viewer-sidebar transform transition-transform duration-300 ease-out ${
          showNavbar ? 'translate-x-0 pointer-events-auto' : '-translate-x-full pointer-events-none'
        }`}
        aria-hidden={!showNavbar}
      >
        <div className="sticky top-0 bg-white border-b p-4 z-10">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-gray-900">页面导航</h3>
            <button
              onClick={() => setShowNavbar(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
        </div>
        <div className="p-4 space-y-3">
          {viewData.items.map((item, index) => (
            <div key={index} className="relative">
              {dragOverIndex === index && (
                <div className="absolute -top-2 left-2 right-2 h-0.5 bg-indigo-500 rounded-full" />
              )}
              <button
                onClick={() => jumpToPage(index)}
                disabled={isNavigationLocked}
                aria-disabled={isNavigationLocked}
                draggable={!isNavigationLocked}
                onDragStart={() => handleDragStart(index)}
                onDragOver={(event) => {
                  if (isNavigationLocked) return;
                  event.preventDefault();
                  setDragOverIndex(index);
                }}
                onDrop={() => handleDrop(index)}
                onDragEnd={handleDragEnd}
                className={`w-full text-left p-3 rounded-lg border-2 transition-all ${
                  index === currentIndex
                    ? 'border-indigo-600 bg-indigo-50'
                    : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                } ${isNavigationLocked ? 'opacity-60 cursor-not-allowed' : ''}`}
              >
                <div className="flex items-start gap-3">
                  {item.type === 'slide' ? (
                    <div className="w-20 h-14 bg-gray-900 rounded flex-shrink-0 overflow-hidden">
                      <img
                        src={`/${item.image_path}`}
                        alt={`Slide ${item.slide_number}`}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ) : item.type === 'demo' ? (
                    <div className="w-20 h-14 bg-indigo-100 rounded flex-shrink-0 flex items-center justify-center">
                      <span className="text-xs text-indigo-600 text-center px-1">
                        交互式演示
                      </span>
                    </div>
                  ) : (
                    <div className="w-20 h-14 bg-green-100 rounded flex-shrink-0 flex items-center justify-center">
                      <span className="text-xs text-green-600 text-center px-1">
                        网页
                      </span>
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-500 mb-1">
                      {index + 1} / {viewData.total_items}
                    </p>
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {item.type === 'slide' ? item.title :
                       item.type === 'demo' ? item.demo_type :
                       item.title}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {item.type === 'slide'
                        ? `幻灯片 ${item.slide_number}`
                        : item.type === 'demo'
                        ? item.reason
                        : item.description}
                    </p>
                  </div>
                </div>
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main className={`max-w-7xl mx-auto px-4 py-8 ppt-viewer-main transition-[margin] duration-300 ${showNavbar ? 'ml-80' : ''}`}>
        {isSlide && (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="relative aspect-video bg-gray-900 flex items-center justify-center">
              <img
                src={`/${currentItem.image_path}`}
                alt={currentItem.title}
                className="max-w-full max-h-full object-contain"
              />
            </div>
            <div className="p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {currentItem.title}
              </h2>
              <p className="text-gray-600">{currentItem.description}</p>
              <p className="text-sm text-indigo-600 mt-4">
                幻灯片 {currentItem.slide_number}
              </p>
            </div>
          </div>
        )}

        {isDemo && (
          <div className={`bg-white rounded-lg shadow-lg overflow-hidden ${isFullscreen ? 'fixed inset-0 z-50 rounded-none' : ''}`}>
            <div className="p-6 border-b bg-indigo-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 bg-indigo-600 text-white text-sm rounded-full">
                    交互式演示
                  </span>
                  <span className="text-sm text-gray-600">
                    幻灯片 {currentItem.slide_number}
                  </span>
                </div>
                {/* Zoom Controls */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={zoomOut}
                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-gray-700 font-bold"
                    title="缩小"
                  >
                    −
                  </button>
                  <button
                    onClick={resetZoom}
                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-gray-700 text-sm"
                    title="重置缩放"
                  >
                    {zoomLevel}%
                  </button>
                  <button
                    onClick={zoomIn}
                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-gray-700 font-bold"
                    title="放大"
                  >
                    +
                  </button>
                  <button
                    onClick={fitToScreen}
                    className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 rounded text-white text-sm"
                    title="适应屏幕"
                  >
                    适应屏幕
                  </button>
                  <button
                    onClick={toggleFullscreen}
                    className="px-3 py-1 bg-gray-800 hover:bg-gray-900 rounded text-white text-sm"
                    title={isFullscreen ? "退出全屏" : "全屏"}
                  >
                    {isFullscreen ? '退出全屏' : '全屏'}
                  </button>
                </div>
              </div>
              {isDemo && <p className="text-gray-700 mt-2">{currentItem.reason}</p>}
              {isDemo && <p className="text-xs text-gray-500 mt-1">
                类型: {currentItem.demo_type}
              </p>}
            </div>
            {/* Demo container with fixed PPT dimensions and zoom */}
            <div
              className="overflow-hidden bg-white"
              style={{
                height: isFullscreen ? 'calc(100vh - 180px)' : '70vh'
              }}
            >
              <div
                className="bg-white"
                style={{
                  width: '100%',
                  height: '100%',
                  position: 'relative'
                }}
              >
                <iframe
                  srcDoc={currentItem.html}
                  ref={demoIframeRef}
                  className="w-full h-full border-0"
                  sandbox="allow-scripts allow-same-origin"
                  title={`幻灯片 ${currentItem.slide_number} 的演示`}
                  style={{
                    transform: `scale(${zoomLevel / 100})`,
                    transformOrigin: 'top left',
                    width: `${10000 / zoomLevel}%`,
                    height: `${10000 / zoomLevel}%`
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {isHTMLSlide && (
          <div className={`bg-white rounded-lg shadow-lg overflow-hidden ${isFullscreen ? 'fixed inset-0 z-50 rounded-none' : ''}`}>
            <div className="p-6 border-b bg-green-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 bg-green-600 text-white text-sm rounded-full">
                    插入的网页
                  </span>
                  <span className="text-sm text-gray-600">
                    {currentItem.title}
                  </span>
                </div>
                {/* Zoom Controls */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={zoomOut}
                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-gray-700 font-bold"
                    title="缩小"
                  >
                    −
                  </button>
                  <button
                    onClick={resetZoom}
                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-gray-700 text-sm"
                    title="重置缩放"
                  >
                    {zoomLevel}%
                  </button>
                  <button
                    onClick={zoomIn}
                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-gray-700 font-bold"
                    title="放大"
                  >
                    +
                  </button>
                  <button
                    onClick={fitToScreen}
                    className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 rounded text-white text-sm"
                    title="适应屏幕"
                  >
                    适应屏幕
                  </button>
                  <button
                    onClick={toggleFullscreen}
                    className="px-3 py-1 bg-gray-800 hover:bg-gray-900 rounded text-white text-sm"
                    title={isFullscreen ? "退出全屏" : "全屏"}
                  >
                    {isFullscreen ? '退出全屏' : '全屏'}
                  </button>
                </div>
              </div>
              <p className="text-gray-700 mt-2">{currentItem.description}</p>
            </div>
            {/* HTML slide container */}
            <div
              className="overflow-hidden bg-white"
              style={{
                height: isFullscreen ? 'calc(100vh - 180px)' : '70vh'
              }}
            >
              <div
                className="bg-white"
                style={{
                  width: '100%',
                  height: '100%',
                  position: 'relative'
                }}
              >
                <iframe
                  srcDoc={currentItem.html}
                  className="w-full h-full border-0"
                  sandbox="allow-scripts allow-same-origin"
                  title={currentItem.title}
                  style={{
                    transform: `scale(${zoomLevel / 100})`,
                    transformOrigin: 'top left',
                    width: `${10000 / zoomLevel}%`,
                    height: `${10000 / zoomLevel}%`
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between mt-8">
          <button
            onClick={goToPrevious}
            disabled={isNavigationLocked || currentIndex === 0}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
          >
            ← 上一页
          </button>

          <div className="text-center">
            <p className="text-gray-600">
              {currentIndex + 1} / {viewData.total_items}
            </p>
            {isSlide && (
              <p className="text-sm text-gray-500">
                {isDemo ? '交互式演示' : `幻灯片 ${(currentItem as SlideItem).slide_number}`}
              </p>
            )}
          </div>

          <button
            onClick={goToNext}
            disabled={isNavigationLocked || currentIndex === viewData.total_items - 1}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
          >
            下一页 →
          </button>
        </div>

        {/* HTML Upload Section */}
        <div className="flex items-center justify-center mt-4">
          <input
            ref={fileInputRef}
            type="file"
            accept=".html"
            onChange={handleHTMLUpload}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadingHTML}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {uploadingHTML ? '上传中...' : '📄 插入网页'}
          </button>
        </div>

        {/* Keyboard hint */}
        <div className="text-center mt-4 text-sm text-gray-500">
          使用方向键导航
        </div>
      </main>
    </div>
  );
}
