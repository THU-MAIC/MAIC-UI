'use client';

import { useState } from 'react';
import type { TemplateOption } from '../../lib/templateTypes';

interface TemplateSelectorProps {
  templateOptions: TemplateOption[];
  onSelectTemplate: (templateId: string) => void;
  selectedTemplateId?: string;
  loading?: boolean;
}

export default function TemplateSelector({
  templateOptions,
  onSelectTemplate,
  selectedTemplateId,
  loading = false,
}: TemplateSelectorProps) {
  const [hoveredTemplate, setHoveredTemplate] = useState<string | null>(null);

  if (templateOptions.length === 0) {
    return (
      <div className="text-center py-8 bg-gray-50 rounded-lg">
        <svg
          className="mx-auto h-12 w-12 text-gray-400 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="text-gray-600">没有找到匹配的模板</p>
        <p className="text-sm text-gray-500 mt-2">系统将使用AI生成内容</p>
      </div>
    );
  }

  const getComplexityColor = (complexity?: string) => {
    switch (complexity) {
      case 'simple':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'complex':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getComplexityText = (complexity?: string) => {
    switch (complexity) {
      case 'simple':
        return '简单';
      case 'medium':
        return '中等';
      case 'complex':
        return '复杂';
      default:
        return '未知';
    }
  };

  const getMatchScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-gray-600';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          选择模板 ({templateOptions.length} 个选项)
        </h3>
        <button
          onClick={() => onSelectTemplate('')}
          className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
        >
          跳过，使用AI生成
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {templateOptions.map((template) => (
          <div
            key={template.template_id}
            className={`relative border-2 rounded-lg p-4 cursor-pointer transition-all ${
              selectedTemplateId === template.template_id
                ? 'border-indigo-500 bg-indigo-50'
                : hoveredTemplate === template.template_id
                ? 'border-gray-300 bg-gray-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => !loading && onSelectTemplate(template.template_id)}
            onMouseEnter={() => setHoveredTemplate(template.template_id)}
            onMouseLeave={() => setHoveredTemplate(null)}
          >
            {selectedTemplateId === template.template_id && (
              <div className="absolute top-2 right-2">
                <svg
                  className="h-5 w-5 text-indigo-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            )}

            {/* Template Name */}
            <h4 className="font-semibold text-gray-900 mb-1 pr-6">
              {template.display_name}
            </h4>

            {/* Match Score */}
            <div className="flex items-center gap-2 mb-2">
              <span className={`text-sm font-medium ${getMatchScoreColor(template.match_score)}`}>
                匹配度: {Math.round(template.match_score * 100)}%
              </span>
              {template.complexity && (
                <span className={`px-2 py-0.5 text-xs rounded-full ${getComplexityColor(template.complexity)}`}>
                  {getComplexityText(template.complexity)}
                </span>
              )}
            </div>

            {/* Match Reason */}
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
              {template.match_reason}
            </p>

            {/* Template Info */}
            <div className="flex items-center justify-between text-xs text-gray-500">
              {template.subject_area && (
                <span>{template.subject_area}</span>
              )}
              {template.usage_count !== undefined && (
                <span>已使用 {template.usage_count} 次</span>
              )}
            </div>

            {/* Preview Button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                // TODO: Open preview modal
                window.open(`/templates/preview/${template.template_id}`, '_blank');
              }}
              className="mt-3 w-full px-3 py-2 text-sm text-indigo-600 border border-indigo-600 rounded hover:bg-indigo-50 transition-colors"
            >
              预览模板
            </button>
          </div>
        ))}
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
          <div className="flex items-center gap-3">
            <svg
              className="animate-spin h-5 w-5 text-indigo-600"
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
            <span className="text-sm font-medium text-gray-700">生成中...</span>
          </div>
        </div>
      )}
    </div>
  );
}
