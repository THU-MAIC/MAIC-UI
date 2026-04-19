'use client';

import { useState, useEffect } from 'react';
import { getPPTStatusWithTemplates, selectPPTTemplates, previewTemplate } from '../../services/templateApi';
import type { PPTTemplateSelection, PPTTemplateOptions, TemplateOption } from '../../lib/templateTypes';

interface PPTTemplateSelectionProps {
  documentId: number;
  onCompleted: () => void;
}

interface SlideTemplateSelection {
  slideNumber: number;
  title?: string;
  description?: string;
  templateOptions: TemplateOption[];
  selectedTemplateId: string;
}

export default function PPTTemplateSelection({ documentId, onCompleted }: PPTTemplateSelectionProps) {
  const [slideSelections, setSlideSelections] = useState<SlideTemplateSelection[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch template options on mount
  useEffect(() => {
    const fetchTemplateOptions = async () => {
      try {
        setLoading(true);
        setError(null);

        const status = await getPPTStatusWithTemplates(documentId);

        if (status.status !== 'awaiting_template_selection') {
          setError(`Document status is "${status.status}", expected "awaiting_template_selection"`);
          setLoading(false);
          return;
        }

        if (!status.template_options) {
          setError('No template options available');
          setLoading(false);
          return;
        }

        // Convert template_options to slide selections
        const selections: SlideTemplateSelection[] = Object.entries(status.template_options).map(
          ([slideNumberStr, options]) => ({
            slideNumber: parseInt(slideNumberStr),
            templateOptions: options,
            selectedTemplateId: '', // Initially no selection
          })
        );

        setSlideSelections(selections);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch template options');
      } finally {
        setLoading(false);
      }
    };

    fetchTemplateOptions();
  }, [documentId]);

  const handleTemplateSelect = (slideNumber: number, templateId: string) => {
    setSlideSelections((prev) =>
      prev.map((slide) =>
        slide.slideNumber === slideNumber
          ? { ...slide, selectedTemplateId: templateId }
          : slide
      )
    );
  };

  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      setError(null);

      // Build template selections map
      const templateSelections: PPTTemplateSelection = {};
      slideSelections.forEach((slide) => {
        if (slide.selectedTemplateId) {
          templateSelections[slide.slideNumber.toString()] = slide.selectedTemplateId;
        }
      });

      if (Object.keys(templateSelections).length === 0) {
        setError('Please select at least one template');
        setSubmitting(false);
        return;
      }

      // Submit template selections
      await selectPPTTemplates(documentId, templateSelections);

      // Call onCompleted callback
      onCompleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit template selections');
      setSubmitting(false);
    }
  };

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

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto bg-white rounded-lg shadow-lg p-8">
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
          <h3 className="text-lg font-semibold text-gray-900 mb-2">正在加载模板选项...</h3>
          <p className="text-gray-600">请稍候</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto bg-white rounded-lg shadow-lg p-8">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">选择演示模板</h2>
        <p className="text-gray-600">
          为幻灯片选择合适的模板来生成交互式演示。已找到 {slideSelections.length} 个需要演示的幻灯片。
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Slide Selections */}
      <div className="space-y-8 mb-8">
        {slideSelections.map((slide) => (
          <div key={slide.slideNumber} className="border border-gray-200 rounded-lg p-6">
            {/* Slide Header */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-1">
                幻灯片 {slide.slideNumber}
              </h3>
              {slide.templateOptions[0]?.demo_reason && (
                <p className="text-sm text-gray-600">{slide.templateOptions[0].demo_reason}</p>
              )}
            </div>

            {/* Template Options */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {/* Skip Option */}
              <div
                className={`relative border-2 rounded-lg p-4 cursor-pointer transition-all ${
                  slide.selectedTemplateId === 'skip'
                    ? 'border-gray-400 bg-gray-100'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleTemplateSelect(slide.slideNumber, 'skip')}
              >
                {slide.selectedTemplateId === 'skip' && (
                  <div className="absolute top-2 right-2">
                    <svg
                      className="h-5 w-5 text-gray-600"
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
                <h4 className="font-semibold text-gray-900 mb-2">跳过</h4>
                <p className="text-sm text-gray-600">不为此幻灯片使用模板</p>
              </div>

              {/* Template Options */}
              {slide.templateOptions.map((template) => (
                <div
                  key={template.template_id}
                  className={`relative border-2 rounded-lg p-4 cursor-pointer transition-all ${
                    slide.selectedTemplateId === template.template_id
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleTemplateSelect(slide.slideNumber, template.template_id)}
                >
                  {slide.selectedTemplateId === template.template_id && (
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

                  {/* Preview Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      // Open preview in new tab - the preview page will call the API
                      window.open(`/templates/preview/${template.template_id}`, '_blank');
                    }}
                    className="w-full px-3 py-2 text-sm text-indigo-600 border border-indigo-600 rounded hover:bg-indigo-50 transition-colors"
                  >
                    预览模板
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Submit Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="flex-1 px-6 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {submitting ? '生成中...' : '生成交互式演示'}
        </button>
      </div>

      {/* Info */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>提示：</strong> 选择模板后，系统将使用选定的模板生成交互式演示。
          可以跳过某些幻灯片不使用模板。生成过程可能需要几分钟时间，完成后将自动跳转到查看页面。
        </p>
      </div>
    </div>
  );
}
