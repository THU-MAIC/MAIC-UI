'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'

// Zhipu models
export type ZhipuModel = 'glm-4.7' | 'glm-4.6'

// Anthropic models
export type AnthropicModel = 'claude-opus-4-6' | 'claude-sonnet-4-6' | 'claude-haiku-4-5-20251001'

// All available AI models
export type AIModel = ZhipuModel | AnthropicModel

// Model provider type
export type ModelProvider = 'zhipu' | 'anthropic'

interface ModelSettingsContextType {
  selectedModel: AIModel
  setSelectedModel: (model: AIModel) => void
  getProvider: () => ModelProvider
}

const ModelSettingsContext = createContext<ModelSettingsContextType | undefined>(undefined)

// Helper function to determine provider from model
function getProviderFromModel(model: AIModel): ModelProvider {
  if (model.startsWith('glm-')) {
    return 'zhipu'
  }
  return 'anthropic'
}

// Valid models list
const VALID_MODELS: AIModel[] = [
  'glm-4.7', 'glm-4.6',
  'claude-opus-4-6', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001'
]

export function ModelSettingsProvider({ children }: { children: React.ReactNode }) {
  const [selectedModel, setSelectedModelState] = useState<AIModel>('glm-4.7')

  // Load saved model preference from localStorage on mount
  useEffect(() => {
    const savedModel = localStorage.getItem('ai_model') as AIModel | null
    // Also check legacy key for backward compatibility
    const legacySavedModel = localStorage.getItem('zhipu_model') as AIModel | null

    const modelToUse = savedModel || legacySavedModel
    if (modelToUse && VALID_MODELS.includes(modelToUse)) {
      setSelectedModelState(modelToUse)
    }
  }, [])

  const setSelectedModel = (model: AIModel) => {
    setSelectedModelState(model)
    localStorage.setItem('ai_model', model)
    // Also update legacy key for backward compatibility
    if (model.startsWith('glm-')) {
      localStorage.setItem('zhipu_model', model)
    }
  }

  const getProvider = (): ModelProvider => {
    return getProviderFromModel(selectedModel)
  }

  const value: ModelSettingsContextType = {
    selectedModel,
    setSelectedModel,
    getProvider,
  }

  return (
    <ModelSettingsContext.Provider value={value}>
      {children}
    </ModelSettingsContext.Provider>
  )
}

export function useModelSettings() {
  const context = useContext(ModelSettingsContext)
  if (context === undefined) {
    throw new Error('useModelSettings must be used within a ModelSettingsProvider')
  }
  return context
}

// Export helper function for use in API calls
export { getProviderFromModel }
