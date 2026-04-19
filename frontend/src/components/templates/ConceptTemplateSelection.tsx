'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { searchConceptTemplates, generateConceptWithTemplate } from '../../services/templateApi';
import TemplateSelector from './TemplateSelector';

interface ConceptTemplateSelectionProps {
  conceptData: {
    subject: string;
    concept_name: string;
    concept_overview: string;
    mastery_points?: string;
    design_idea?: string;
  };
  metadata?: {
    grade_level?: number;
    description?: string;
    interests?: string;
  };
}

export default function ConceptTemplateSelection({
  conceptData,
  metadata = {},
}: ConceptTemplateSelectionProps) {
  const router = useRouter();

  const [templateOptions, setTemplateOptions] = useState<any[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search for templates on mount
  useState(() => {
    const searchTemplates = async () => {
      try {
        setSearching(true);
        setError(null);

        const result = await searchConceptTemplates(
          conceptData.subject,
          conceptData.concept_name,
          conceptData.concept_overview,
          metadata.grade_level,
          5
        );

        if (result.status === 'success' && result.template_options) {
          setTemplateOptions(result.template_options);
        } else {
          setError('未找到匹配的模板');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '搜索模板失败');
      } finally {
        setSearching(false);
      }
    };

    searchTemplates();
  });

  const handleSelectTemplate = async (templateId: string) => {
    if (!templateId) {
      // User chose to skip, redirect to concept upload without template
      router.push('/document-upload?mode=concept');
      return;
    }

    setSelectedTemplateId(templateId);
  };

  const handleGenerate = async () => {
    if (!selectedTemplateId) return;

    try {
      setLoading(true);
      setError(null);

      const result = await generateConceptWithTemplate(
        conceptData.subject,
        conceptData.concept_name,
        conceptData.concept_overview,
        conceptData.mastery_points || '',
        conceptData.design_idea || '',
        selectedTemplateId,
        metadata.grade_level,
        metadata.description,
        false, // is_public
        metadata.interests
      );

      if (result.id) {
        // Redirect to document viewer
        router.push(`/document/${result.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成失败');
      setLoading(false);
    }
  };

  if (searching) {
    return (
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-8">
        <div className="flex flex-col items-center justify-center py-12">
          <svg
            className="animate-spin h-12 w-12 text-indigo-600 mb-4"
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
          <h3 className="text-lg font-semibold text-gray-900 mb-2">正在搜索合适的模板...</h3>
          <p className="text-gray-600">根据您的概念内容查找最佳匹配</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-8">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">选择网站模板</h2>
        <p className="text-gray-600">
          为"{conceptData.concept_name}"选择一个模板来生成交互式学习网站
        </p>
      </div>

      {/* Concept Info */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-700">学科：</span>
            <span className="text-gray-900">{conceptData.subject}</span>
          </div>
          {metadata.grade_level && (
            <div>
              <span className="font-medium text-gray-700">年级：</span>
              <span className="text-gray-900">{metadata.grade_level}</span>
            </div>
          )}
        </div>
        {conceptData.concept_overview && (
          <div className="mt-3 text-sm">
            <span className="font-medium text-gray-700">概述：</span>
            <p className="text-gray-900 mt-1">{conceptData.concept_overview}</p>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Template Selector */}
      <div className="mb-6">
        <TemplateSelector
          templateOptions={templateOptions}
          onSelectTemplate={handleSelectTemplate}
          selectedTemplateId={selectedTemplateId}
          loading={loading}
        />
      </div>

      {/* Generate Button (shown when template is selected) */}
      {selectedTemplateId && (
        <div className="flex gap-3">
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="flex-1 px-6 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {loading ? '生成中...' : '生成交互式网站'}
          </button>
          <button
            onClick={() => setSelectedTemplateId('')}
            disabled={loading}
            className="px-6 py-3 bg-gray-100 text-gray-700 font-semibold rounded-lg hover:bg-gray-200"
          >
            返回
          </button>
        </div>
      )}

      {/* Info */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>下一步：</strong> 选择模板后，系统将使用选定的模板生成网站。
          生成过程可能需要几分钟时间，完成后将自动跳转到查看页面。
        </p>
      </div>
    </div>
  );
}
