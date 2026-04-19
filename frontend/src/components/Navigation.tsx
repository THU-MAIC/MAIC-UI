'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useModelSettings, AIModel } from '@/components/providers/ModelSettingsProvider'

interface NavigationProps {
  user?: {
    full_name?: string
    username?: string
  }
  onLogout?: () => void
}

export default function Navigation({ user, onLogout }: NavigationProps) {
  const pathname = usePathname()
  const { selectedModel, setSelectedModel } = useModelSettings()
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false)

  const navLinks = [
    { href: '/dashboard', label: '交互资源生成' },
    { href: '/ppt-upload', label: '上传PPT' },
    { href: '/templates', label: '模板库' },
    { href: '/public_documents', label: '查看公开文档' },
  ]

  const isActive = (href: string) => {
    return pathname === href
  }

  const models: { value: AIModel; label: string; description: string; provider: string }[] = [
    {
      value: 'glm-4.7',
      label: 'GLM-4.7',
      description: '优先使用获得最佳效果',
      provider: 'Zhipu'
    },
    {
      value: 'glm-4.6',
      label: 'GLM-4.6',
      description: '如遇并发限制可切换',
      provider: 'Zhipu'
    },
    {
      value: 'claude-opus-4-6',
      label: 'Claude Opus 4.6',
      description: '最强推理能力，适合复杂任务',
      provider: 'Anthropic'
    },
    {
      value: 'claude-sonnet-4-6',
      label: 'Claude Sonnet 4.6',
      description: '平衡性能与速度',
      provider: 'Anthropic'
    },
    {
      value: 'claude-haiku-4-5-20251001',
      label: 'Claude Haiku 4.5',
      description: '快速响应，适合简单任务',
      provider: 'Anthropic'
    },
  ]

  return (
    <div className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center space-x-8">
            <h1 className="text-2xl font-bold text-gray-900">
              MAIC-UI
            </h1>
            <nav className="flex space-x-4">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive(link.href)
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            {/* Model Selector */}
            <div className="relative">
              <button
                onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
                className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                <span>AI模型:</span>
                <span className="text-blue-600 font-semibold">
                  {models.find(m => m.value === selectedModel)?.label || selectedModel}
                </span>
                <svg
                  className={`w-4 h-4 transition-transform ${isModelDropdownOpen ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {isModelDropdownOpen && (
                <div className="absolute right-0 mt-2 w-72 bg-white border border-gray-300 rounded-md shadow-lg z-50">
                  <div className="py-1">
                    {/* Zhipu Models */}
                    <div className="px-4 py-2 text-xs font-semibold text-gray-500 bg-gray-50 border-b border-gray-200">
                      Zhipu AI (智谱)
                    </div>
                    {models.filter(m => m.provider === 'Zhipu').map((model) => (
                      <button
                        key={model.value}
                        onClick={() => {
                          setSelectedModel(model.value)
                          setIsModelDropdownOpen(false)
                        }}
                        className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                          selectedModel === model.value ? 'bg-blue-50 border-l-4 border-blue-600' : ''
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-semibold text-gray-900">{model.label}</div>
                            <div className="text-xs text-gray-500 mt-1">{model.description}</div>
                          </div>
                          {selectedModel === model.value && (
                            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      </button>
                    ))}
                    {/* Anthropic Models */}
                    <div className="px-4 py-2 text-xs font-semibold text-gray-500 bg-gray-50 border-b border-t border-gray-200">
                      Anthropic (Claude)
                    </div>
                    {models.filter(m => m.provider === 'Anthropic').map((model) => (
                      <button
                        key={model.value}
                        onClick={() => {
                          setSelectedModel(model.value)
                          setIsModelDropdownOpen(false)
                        }}
                        className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                          selectedModel === model.value ? 'bg-purple-50 border-l-4 border-purple-600' : ''
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-semibold text-gray-900">{model.label}</div>
                            <div className="text-xs text-gray-500 mt-1">{model.description}</div>
                          </div>
                          {selectedModel === model.value && (
                            <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {user && (
              <span className="text-sm text-gray-600">
                欢迎，{user.full_name || user.username}！
              </span>
            )}
            {onLogout && (
              <button
                onClick={onLogout}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                退出登录
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
