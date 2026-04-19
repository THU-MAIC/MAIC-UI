'use client'

import React, { useEffect, useRef, useState, useCallback } from 'react'
import { WebEditorAPI, startStatusPolling } from './WebEditorAPI'
import { DOMHighlighter } from './DOMHighlighter'
import { EventManager } from './EventManager'
import { CitationListManager } from './CitationListManager'
import { VersionManager } from './VersionManager'
import { WebEditorProps, EditStatus, VersionType, CitationListItem, ModelType, MODEL_OPTIONS, MODEL_TYPE_TO_LABEL } from './types'
import './WebEditor.css'

// Export types for external use
export type { DocumentVersion, WebEditorProps } from './types'
export { WebEditorAPI } from './WebEditorAPI'
export { DOMHighlighter } from './DOMHighlighter'
export { EventManager } from './EventManager'
export { CitationListManager } from './CitationListManager'
export { VersionManager } from './VersionManager'

const config = {
	buttonPosition: 'bottom-right',
	highlightColor: '#f00',
	copyNotification: true,
	disableAnimations: false,
	excludeSelectors: [
		'.advertisement',
		'[data-no-edit]',
		'[data-no-edit] *',
		'.ppt-viewer-frame',
		'.ppt-viewer-frame *',
		'.ppt-viewer-header',
		'.ppt-viewer-header *',
		'.ppt-viewer-sidebar',
		'.ppt-viewer-sidebar *',
		'.ppt-viewer-main',
		'.ppt-viewer-main *'
	]
}

// Help content from help.md
const HELP_CONTENT = [
	{
		question: 'Q1：如何使用编辑模式？',
		answer: [
			'点击<b>"编辑模式"按钮</b>进入编辑模式，',
			'点击<b>"退出编辑"按钮</b>或按下<b>ESC键</b>退出编辑，',
			'点击<b>"开始编辑"按钮</b>之后编辑任务进入后台运行，期间无法进行翻页操作。',
			'编辑任务完成后右下角按钮会显示<b>"编辑已完成！"</b>，此时点击该按钮，会在上方出现版本选择组件。',
			'在版本选择组件当中点击<b>"修改前"/"修改后"按钮</b>，并点击<b>"保存该版本"按钮</b>之后才能够进行下一步操作。如果修改的效果不若您所期望，可以保存<b>"修改前"</b>版本之后再次进行编辑。'
		]
	},
	{
		question: 'Q2：如何添加组件引用？',
		answer: '点击按钮进入编辑模式，将鼠标放置在网页组件上，解析出的网页组件会实时添加高亮遮罩，<b>点击即可引用该组件</b>（网页组件中央序号为引用编号）。如果选择的组件不准确，不妨选择它的上一级、包含它的组件作为引用。'
	},
	{
		question: 'Q3：如何正确描述自己的需求？',
		answer: '使用<b>祈使句式</b>（如"将xxx的位置修改为xxx"），尽可能精确地描述自己的需求。'
	},
	{
		question: 'Q4：什么时候不需要思考模式？',
		answer: '一些简单的修改，比如<b>文字内容修改、组件样式修改</b>可以不打开思考模式，响应时间一般在<b>5-20s</b>。由于非思考模式编辑较快，<b>建议先不打开思考模式</b>进行几次编辑，如果发现修改结果不够理想，再打开思考模式试试。'
	},
	{
		question: 'Q5：什么时候需要开启思考模式？',
		answer: '困难的修改。比如<b>画布当中图形位置的修改、交互逻辑修改</b>建议打开思考模式，响应时间一般在<b>1-3min</b>。'
	}
]

export function WebEditor({
	targetIframeRef,
	documentId,
	isPublic = false,
	resourceType = 'web',
	slideNumber,
	onEditStatusChange,
	onEditModeChange,
	onVersionSaved
}: WebEditorProps) {
	// State
	const [isEditMode, setIsEditMode] = useState(false)
	const [noteInput, setNoteInput] = useState('')
	const [citationItems, setCitationItems] = useState<CitationListItem[]>([])
	const [showVersionToggle, setShowVersionToggle] = useState(false)
	const [currentVersion, setCurrentVersion] = useState<VersionType>('before')
	const [originalHtml, setOriginalHtml] = useState<string>('')
	const [modifiedHtml, setModifiedHtml] = useState<string>('')
	const [isLoading, setIsLoading] = useState(false)
	const [loadingMessage, setLoadingMessage] = useState('')
	const [isEditingStarted, setIsEditingStarted] = useState(false)
	const [editStatus, setEditStatus] = useState<EditStatus>('idle')
	const [isThinkingMode, setIsThinkingMode] = useState(false)
	const [showHelpModal, setShowHelpModal] = useState(false)
	const [showHistory, setShowHistory] = useState(false)
	const [historyItems, setHistoryItems] = useState<string[]>([])
	const [selectedModel, setSelectedModel] = useState<ModelType>('glm-4.7')
	const [showModelDropdown, setShowModelDropdown] = useState(false)
	// Track the effective document ID (may differ from prop after saving new versions)
	const [effectiveDocumentId, setEffectiveDocumentId] = useState<number | undefined>(documentId)

	// Refs
	const textareaRef = useRef<HTMLTextAreaElement | null>(null)
	const pollingIntervalRef = useRef<(() => void) | null>(null)
	const editStatusRef = useRef<EditStatus>('idle')
	const historyDropdownRef = useRef<HTMLDivElement | null>(null)
	const providerDropdownRef = useRef<HTMLDivElement | null>(null)

	// Stable documentId for history key (does not change when versions are saved)
	const stableDocumentIdRef = useRef(documentId)

	// Module instances
	const highlighterRef = useRef<DOMHighlighter | null>(null)
	const citationListManagerRef = useRef<CitationListManager | null>(null)
	const eventManagerRef = useRef<EventManager | null>(null)
	const versionManagerRef = useRef<VersionManager | null>(null)
	const apiRef = useRef<WebEditorAPI | null>(null)

	// Sync effectiveDocumentId when prop changes
	useEffect(() => {
		setEffectiveDocumentId(documentId)
	}, [documentId])

	// Keep editStatusRef in sync with editStatus state
	useEffect(() => {
		editStatusRef.current = editStatus
	}, [editStatus])

	// Initialize modules
	useEffect(() => {
		highlighterRef.current = new DOMHighlighter()
		highlighterRef.current.setTargetIframe(targetIframeRef || null)
		citationListManagerRef.current = new CitationListManager()
		eventManagerRef.current = new EventManager(
			highlighterRef.current,
			citationListManagerRef.current,
			targetIframeRef
		)
		apiRef.current = new WebEditorAPI(effectiveDocumentId, isPublic, resourceType, slideNumber)

		if (effectiveDocumentId && resourceType === 'web') {
			versionManagerRef.current = new VersionManager(effectiveDocumentId, isPublic)
		} else {
			versionManagerRef.current = null
		}

		return () => {
			// Cleanup will be done in exitEditMode
		}
	}, [effectiveDocumentId, isPublic, resourceType, slideNumber, targetIframeRef])

	// Sync citation items with React state
	const syncCitationItems = useCallback(() => {
		if (citationListManagerRef.current) {
			setCitationItems(citationListManagerRef.current.getAll())
		}
	}, [])

	// Initialize event manager callbacks
	useEffect(() => {
		if (eventManagerRef.current) {
			eventManagerRef.current.setEditModeState(isEditMode, setIsEditMode)
			eventManagerRef.current.setOnCitationAdd(() => {
				syncCitationItems()
			})
		}
	}, [isEditMode, syncCitationItems])

	// Handle keyboard escape key
	useEffect(() => {
		const handleEscape = (e: KeyboardEvent) => {
			if (e.key === 'Escape' && isEditMode) {
				setIsEditMode(false)
			}
		}

		document.addEventListener('keydown', handleEscape)
		return () => document.removeEventListener('keydown', handleEscape)
	}, [isEditMode])

	// Effect for edit mode changes
	useEffect(() => {
		if (isEditMode) {
			enterEditMode()
		} else {
			exitEditMode()
		}

		onEditModeChange?.(isEditMode)

		return () => {
			if (isEditMode) {
				exitEditMode()
			}
		}
	}, [isEditMode, onEditModeChange, targetIframeRef?.current])

	// Cleanup SSE/polling on unmount
	useEffect(() => {
		return () => {
			if (pollingIntervalRef.current) {
				pollingIntervalRef.current()
			}
		}
	}, [])

	// History management
	// Use stableDocumentIdRef (initial documentId from first mount) to ensure consistent key
	// even when documentId prop changes due to version saves (e.g., PPT viewer updates activeDocumentId)
	const getHistoryKey = useCallback(() => {
		const id = stableDocumentIdRef.current
		if (!id) return ''
		return `webeditor_history_${resourceType}_${id}`
	}, [resourceType])

	const loadHistory = useCallback(() => {
		const key = getHistoryKey()
		if (!key) {
			setHistoryItems([])
			return
		}
		try {
			const stored = sessionStorage.getItem(key)
			const items = stored ? JSON.parse(stored) : []
			setHistoryItems(Array.isArray(items) ? items : [])
		} catch {
			setHistoryItems([])
		}
	}, [getHistoryKey])

	const saveToHistory = useCallback((instruction: string) => {
		if (!instruction.trim()) return
		const key = getHistoryKey()
		if (!key) return
		try {
			const stored = sessionStorage.getItem(key)
			const existing: string[] = stored ? JSON.parse(stored) : []
			const filtered = existing.filter(item => item !== instruction)
			const updated = [instruction, ...filtered].slice(0, 20)
			sessionStorage.setItem(key, JSON.stringify(updated))
			setHistoryItems(updated)
		} catch {
			// ignore sessionStorage errors
		}
	}, [getHistoryKey])

	useEffect(() => {
		loadHistory()
	}, [loadHistory])

	// Clean up sessionStorage history on page unload (refresh / navigate away)
	useEffect(() => {
		const key = getHistoryKey()
		if (!key) return

		const handleBeforeUnload = () => {
			sessionStorage.removeItem(key)
		}
		window.addEventListener('beforeunload', handleBeforeUnload)
		return () => {
			window.removeEventListener('beforeunload', handleBeforeUnload)
		}
	}, [getHistoryKey])

	useEffect(() => {
		if (!showHistory) return
		const handleClickOutside = (e: MouseEvent) => {
			if (historyDropdownRef.current && !historyDropdownRef.current.contains(e.target as Node)) {
				setShowHistory(false)
			}
		}
		document.addEventListener('mousedown', handleClickOutside)
		return () => document.removeEventListener('mousedown', handleClickOutside)
	}, [showHistory])

	// Model dropdown click outside handler
	useEffect(() => {
		if (!showModelDropdown) return
		const handleClickOutside = (e: MouseEvent) => {
			if (providerDropdownRef.current && !providerDropdownRef.current.contains(e.target as Node)) {
				setShowModelDropdown(false)
			}
		}
		document.addEventListener('mousedown', handleClickOutside)
		return () => document.removeEventListener('mousedown', handleClickOutside)
	}, [showModelDropdown])

	// Enter edit mode
	const enterEditMode = () => {
		const highlighter = highlighterRef.current
		const eventManager = eventManagerRef.current
		const citationListManager = citationListManagerRef.current

		if (!highlighter || !eventManager || !citationListManager) return

		citationListManager.clear()
		highlighter.disableDynamicElements(targetIframeRef)
		highlighter.createHighlightOverlay()
		highlighter.createModeIndicator()
		eventManager.attachDocumentListeners(document, null)
		eventManager.registerIframes()

		// Listen to scroll events
		const updatePinnedPositions = () => {
			highlighter.updatePinnedPositions(citationListManager.getHead())
		}
		window.addEventListener('scroll', updatePinnedPositions, true)

		// Listen to iframe scroll
		const targetDoc = targetIframeRef?.current?.contentDocument
		if (targetDoc) {
			targetDoc.addEventListener('scroll', updatePinnedPositions, true)
		}

		// Store the function for cleanup
		;(window as any).__updatePinnedPositions = updatePinnedPositions
	}

	// Exit edit mode
	const exitEditMode = () => {
		const highlighter = highlighterRef.current
		const eventManager = eventManagerRef.current
		const citationListManager = citationListManagerRef.current

		if (!highlighter || !eventManager || !citationListManager) return

		highlighter.restoreDynamicElements(targetIframeRef)
		highlighter.removeHighlightOverlay()
		highlighter.removeTooltip()
		highlighter.clearCitationArtifacts(citationListManager.getHead())
		highlighter.resetNumberBadges()
		citationListManager.clear()
		syncCitationItems()
		highlighter.removeModeIndicator()
		eventManager.detachDocumentListeners(document, null)
		eventManager.unregisterIframes()

		const mask = document.querySelector('.editor-mask')
		if (mask) mask.remove()

		// Clear input and conditionally reset edit state
		setNoteInput('')
		// Only reset these states if we're not in the middle of editing or viewing results
		// This prevents the version toggle from being hidden when the effect re-runs
		const currentEditStatus = editStatusRef.current
		if (currentEditStatus !== 'processing' && currentEditStatus !== 'completed') {
			setIsEditingStarted(false)
			setShowVersionToggle(false)
		}

		// Remove scroll listeners
		const updatePinnedPositions = (window as any).__updatePinnedPositions
		if (updatePinnedPositions) {
			window.removeEventListener('scroll', updatePinnedPositions, true)
			const targetDoc = targetIframeRef?.current?.contentDocument
			if (targetDoc) {
				targetDoc.removeEventListener('scroll', updatePinnedPositions, true)
			}
			delete (window as any).__updatePinnedPositions
		}
	}

	// Remove citation by ID
	const removeCitationById = (id: number) => {
		const citationListManager = citationListManagerRef.current
		const highlighter = highlighterRef.current

		if (!citationListManager || !highlighter) return

		const removedItem = citationListManager.remove(id)
		if (removedItem) {
			removedItem.pageBadge?.remove()
			removedItem.highlightOverlay?.remove()
			syncCitationItems()
		}
	}

	// Get button label based on status
	const getButtonLabel = () => {
		if (editStatus === 'processing') {
			return isThinkingMode ? '正在编辑中（预计1-2min）' : '正在编辑中（预计5-20s）'
		}
		if (editStatus === 'completed') {
			return '编辑已完成！'
		}
		return isEditMode ? '退出编辑' : '编辑模式'
	}
	const buttonLabel = getButtonLabel()

	// Check edit status on mount
	const checkEditStatus = useCallback(async () => {
		if (!effectiveDocumentId || !apiRef.current) return

		try {
			const statusResult = await apiRef.current.checkEditStatus()

			console.log('[WebEditor] 📊 检查编辑状态:', statusResult.status)

			if (statusResult.status === 'processing') {
				setEditStatus('processing')
				onEditStatusChange?.('processing')
				setIsEditingStarted(true)

				const targetDoc = targetIframeRef?.current?.contentDocument
				if (targetDoc) {
					setOriginalHtml(targetDoc.documentElement.outerHTML)
				}

				startStatusPollingInternal()
			} else if (statusResult.status === 'ready' && statusResult.modified_html) {
				setEditStatus('completed')
				onEditStatusChange?.('completed')
				setIsEditingStarted(true)
				setModifiedHtml(statusResult.modified_html)
				setShowVersionToggle(true)
				setCurrentVersion('after')

				const targetDoc = targetIframeRef?.current?.contentDocument
				if (targetDoc) {
					setOriginalHtml(targetDoc.documentElement.outerHTML)
				}

				// Automatically update iframe to show modified version
				const targetIframe = targetIframeRef?.current
				if (targetIframe && statusResult.modified_html) {
					targetIframe.srcdoc = statusResult.modified_html
					highlighterRef.current?.invalidateIframeContent()
				}
			}
		} catch (error) {
			console.error('[WebEditor] 检查编辑状态失败:', error)
		}
	}, [effectiveDocumentId, onEditStatusChange, resourceType, slideNumber, targetIframeRef])

	// Start SSE status streaming (with polling fallback)
	const startStatusPollingInternal = useCallback(() => {
		if (pollingIntervalRef.current) {
			pollingIntervalRef.current()
		}

		const highlighter = highlighterRef.current
		if (!highlighter) return

		pollingIntervalRef.current = startStatusPolling({
			documentId: effectiveDocumentId,
			isPublic,
			resourceType,
			slideNumber,
			onProcessing: () => {
				console.log('[WebEditor] Processing...')
			},
			onCompleted: (modifiedHtmlResult) => {
				setModifiedHtml(modifiedHtmlResult)
				setEditStatus('completed')
				onEditStatusChange?.('completed')
				setShowVersionToggle(true)
				setCurrentVersion('after')
				// Automatically update iframe to show modified version
				const targetIframe = targetIframeRef?.current
				if (targetIframe && modifiedHtmlResult) {
					targetIframe.srcdoc = modifiedHtmlResult
					highlighter.invalidateIframeContent()
				}
				highlighter.showNotification('✅ AI修改完成！已自动切换到修改后版本')
			},
			onError: (error) => {
				setEditStatus('idle')
				onEditStatusChange?.('idle')
				setIsEditingStarted(false)
				highlighter.showNotification(`❌ 修改失败: ${error}`)
			},
			onTimeout: () => {
				setEditStatus('idle')
				onEditStatusChange?.('idle')
				setIsEditingStarted(false)
				highlighter.showNotification('❌ 修改超时，请重试')
			}
		})
	}, [effectiveDocumentId, isPublic, onEditStatusChange, resourceType, slideNumber])

	// Check edit status on mount
	useEffect(() => {
		const timer = setTimeout(() => {
			checkEditStatus()
		}, 1000)

		return () => clearTimeout(timer)
	}, [checkEditStatus])

	// Handle start editing
	const handleStartEditing = async () => {
		const highlighter = highlighterRef.current
		const api = apiRef.current
		const citationListManager = citationListManagerRef.current

		if (!highlighter || !api || !citationListManager) return

		if (noteInput.trim()) {
			const citationsSnapshot = citationListManager.getAll()
			saveToHistory(noteInput.trim())
			exitEditMode()
			setIsEditMode(false)
			setEditStatus('processing')
			onEditStatusChange?.('processing')
			setIsEditingStarted(true)

			const targetDoc = targetIframeRef?.current?.contentDocument
			if (targetDoc) {
				const currentHtml = targetDoc.documentElement.outerHTML
				setOriginalHtml(currentHtml)

				try {
					if (effectiveDocumentId) {
						await api.submitEditRequest(
							effectiveDocumentId,
							citationsSnapshot,
							noteInput.trim(),
							isThinkingMode,
							selectedModel
						)
						highlighter.showNotification('⏳ 已提交编辑请求，AI正在处理中...')
						startStatusPollingInternal()
					} else {
						setModifiedHtml(currentHtml)
						setEditStatus('completed')
						onEditStatusChange?.('completed')
						setCurrentVersion('after')
						// Automatically update iframe to show modified version
						const targetIframe = targetIframeRef?.current
						if (targetIframe && currentHtml) {
							targetIframe.srcdoc = currentHtml
							highlighterRef.current?.invalidateIframeContent()
						}
					}
				} catch (error) {
					console.error('Edit failed:', error)
					setEditStatus('idle')
					onEditStatusChange?.('idle')
					setIsEditingStarted(false)
					highlighter.showNotification(`❌ 修改失败: ${error instanceof Error ? error.message : '未知错误'}`)
				}
			}
		} else {
			if (!isEditMode) {
				setIsEditMode(true)
			}
			textareaRef.current?.focus()
		}
	}

	// Handle version toggle
	const handleVersionToggle = (version: VersionType) => {
		setCurrentVersion(version)
		const targetIframe = targetIframeRef?.current
		if (targetIframe) {
			const htmlToShow = version === 'before' ? originalHtml : modifiedHtml
			if (htmlToShow) {
				targetIframe.srcdoc = htmlToShow
				// Notify highlighter that iframe content has been replaced
				highlighterRef.current?.invalidateIframeContent()
			}
		}
	}

	// Handle keep version
	const handleKeepVersion = async () => {
		const highlighter = highlighterRef.current
		const api = apiRef.current
		const isPptEditing = resourceType === 'ppt'

		// If keeping 'before' version, notify backend to clear edit state (no new file created)
		if (currentVersion === 'before') {
			// Call API to clear backend edit state so it won't show version toggle on page reload
			if (effectiveDocumentId && api) {
				try {
					const currentPath = window.location.pathname
					const isPublicRoute = isPublic || currentPath.includes('/public/document/')
					await api.keepVersion(effectiveDocumentId, 'before', isPublicRoute, slideNumber)
				} catch (error) {
					console.error('[WebEditor] Failed to clear backend edit state:', error)
				}
			}

			setModifiedHtml('')
			setCurrentVersion('before')
			setShowVersionToggle(false)
			setEditStatus('idle')
			onEditStatusChange?.('idle')
			setIsEditingStarted(false)
			setNoteInput('')
			highlighter?.showNotification('✅ 已保留修改前版本')
			return
		}

		if (!effectiveDocumentId) {
			highlighter?.showNotification('无法保存：缺少文档ID')
			return
		}

		const versionManager = versionManagerRef.current

		if (!highlighter || !api) return

		const versionName = '修改后'
		const htmlToSave = modifiedHtml

		setIsLoading(true)
		setLoadingMessage(`正在保存${versionName}版本...`)

		try {
			const currentPath = window.location.pathname
			const isPublicRoute = isPublic || currentPath.includes('/public/document/')

			if (isPptEditing) {
				await api.keepVersion(
					effectiveDocumentId,
					currentVersion,
					isPublicRoute,
					slideNumber
				)
				await api.keepVersion(
					effectiveDocumentId,
					'before',
					isPublicRoute,
					slideNumber
				)
				onVersionSaved?.()
			} else if (versionManager) {
				const result = await versionManager.keepVersion(
					currentVersion,
					htmlToSave,
					noteInput.trim() || '无修改指令',
					() => api.keepVersion(
						effectiveDocumentId,
						currentVersion,
						isPublicRoute
					),
					isPublicRoute
				)

				// Update effectiveDocumentId to the new version for subsequent edits
				if (result.newDocumentId) {
					console.log('[WebEditor] 📝 Updating effectiveDocumentId from', effectiveDocumentId, 'to', result.newDocumentId)
					setEffectiveDocumentId(result.newDocumentId)
					api.setDocumentId(result.newDocumentId)
				}

				const updatedVersions = await versionManager.refreshVersions()
				const newVersion = result.newDocumentId
					? updatedVersions.find(v => v.documentId === result.newDocumentId)
					: updatedVersions.find(v => v.isCurrent)
				if (newVersion) {
					onVersionSaved?.(newVersion)
				}

				if (isPublicRoute && result.newDocumentId) {
					highlighter.showNotification(`✅ 已创建新版本文档 (ID: ${result.newDocumentId})`)
				} else {
					highlighter.showNotification(`✅ 已保留${versionName}版本`)
				}
			}

			// Update frontend state with modified version
			if (modifiedHtml) {
				setOriginalHtml(modifiedHtml)
				const targetIframe = targetIframeRef?.current
				if (targetIframe) {
					targetIframe.srcdoc = modifiedHtml
					// Notify highlighter that iframe content has been replaced
					highlighterRef.current?.invalidateIframeContent()
				}
			}

			setModifiedHtml('')
			setCurrentVersion('before')
			setShowVersionToggle(false)

			if (isPptEditing) {
				highlighter.showNotification(`✅ 已保留${versionName}版本`)
			}

			setEditStatus('idle')
			onEditStatusChange?.('idle')
			setIsEditingStarted(false)
			setNoteInput('')
		} catch (error) {
			console.error('❌ Save version error:', error)
			const errorMessage = error instanceof Error ? error.message : '保存失败'
			highlighter.showNotification(`❌ 保存失败: ${errorMessage}`)
		} finally {
			setIsLoading(false)
			setLoadingMessage('')
		}
	}

	return (
		<>
			{/* Loading overlay */}
			{isLoading && (
				<div className="editor-loading-overlay">
					<div className="editor-loading-spinner"></div>
					<div className="editor-loading-text">{loadingMessage}</div>
				</div>
			)}

			{/* Version toggle panel */}
			{showVersionToggle && (
				<div className="version-toggle-container">
					<span className="version-label">查看版本：</span>
					<button
						type="button"
						className={`version-toggle-btn ${currentVersion === 'before' ? 'active' : ''}`}
						onClick={() => handleVersionToggle('before')}
					>
						修改前
					</button>
					<button
						type="button"
						className={`version-toggle-btn ${currentVersion === 'after' ? 'active' : ''}`}
						onClick={() => handleVersionToggle('after')}
					>
						修改后
					</button>
					<button
						type="button"
						className="keep-version-btn"
						onClick={handleKeepVersion}
					>
						✓ 保留该版本
					</button>
				</div>
			)}

			{/* Editor mode container */}
			<div
				id="editor-mode-container"
				style={{
					bottom: config.buttonPosition.includes('bottom') ? 20 : undefined,
					top: config.buttonPosition.includes('top') ? 20 : undefined,
					right: config.buttonPosition.includes('right') ? 20 : undefined,
					left: config.buttonPosition.includes('left') ? 20 : undefined
				}}
			>
				{/* Citation badges */}
				{citationItems.length > 0 && (
					<div className="citation-badge-list">
						{citationItems.map(item => (
							<div key={item.id} className="citation-badge">
								{item.index}
								<button
									className="citation-badge-remove"
									type="button"
									onClick={() => removeCitationById(item.id)}
									aria-label="删除引用"
									disabled={isEditingStarted || isLoading}
									style={{
										opacity: isEditingStarted || isLoading ? 0.5 : 1,
										cursor: isEditingStarted || isLoading ? 'not-allowed' : 'pointer'
									}}
								>
									×
								</button>
							</div>
						))}
					</div>
				)}

				{/* Editor controls */}
				<div className="editor-buttons-row">
					<div className="editor-mode-controls">
						<div className={`editor-mode-panel ${isEditMode ? 'active' : ''}`}>
							<div className="history-dropdown-wrapper" ref={historyDropdownRef}>
								<textarea
									id="editor-mode-input"
									placeholder="输入改动指示..."
									value={noteInput}
									onChange={(e) => setNoteInput(e.target.value)}
									onKeyDown={(e) => {
										if (e.key === 'Enter' && !e.shiftKey && !e.altKey && !e.metaKey) {
											e.preventDefault()
											handleStartEditing()
										}
									}}
									rows={1}
									maxLength={500}
									ref={textareaRef}
									disabled={isEditingStarted || isLoading}
									style={{ opacity: isEditingStarted || isLoading ? 0.7 : 1 }}
								/>
								{historyItems.length > 0 && (
									<button
										type="button"
										className={`history-toggle-btn ${showHistory ? 'active' : ''}`}
										onClick={() => setShowHistory(prev => !prev)}
										title="历史指令"
										disabled={isEditingStarted || isLoading}
									>
										▾
									</button>
								)}
								{showHistory && historyItems.length > 0 && (
									<div className="history-dropdown">
										{historyItems.map((item, index) => (
											<div
												key={index}
												className="history-dropdown-item"
												onClick={() => {
													setNoteInput(item)
													setShowHistory(false)
													textareaRef.current?.focus()
												}}
											>
												{item}
											</div>
										))}
									</div>
								)}
							</div>
							<div className="provider-dropdown-wrapper" ref={providerDropdownRef}>
								<button
									type="button"
									className={`provider-select-btn ${showModelDropdown ? 'active' : ''}`}
									onClick={() => setShowModelDropdown(prev => !prev)}
									disabled={isEditingStarted || isLoading}
									title="选择AI模型"
								>
									{MODEL_TYPE_TO_LABEL[selectedModel]}
									<span className="provider-select-arrow">▾</span>
								</button>
								{showModelDropdown && (
									<div className="provider-dropdown">
										{MODEL_OPTIONS.map((option) => (
											<div
												key={option.value}
												className={`provider-dropdown-item ${selectedModel === option.value ? 'selected' : ''}`}
												onClick={() => {
													setSelectedModel(option.value)
													setShowModelDropdown(false)
												}}
											>
												{option.label}
											</div>
										))}
									</div>
								)}
							</div>
							<button
								type="button"
								className={`editor-thinking-toggle ${isThinkingMode ? 'active' : ''}`}
								onClick={() => setIsThinkingMode(prev => !prev)}
								disabled={isEditingStarted || isLoading}
								aria-pressed={isThinkingMode}
								title={isThinkingMode ? '已启用思考模式' : '思考模式已关闭'}
							>
								思考模式
							</button>
							<button
								id="editor-start-btn"
								type="button"
								onClick={handleStartEditing}
								disabled={isEditingStarted || isLoading}
								style={{ opacity: isEditingStarted || isLoading ? 0.5 : 1 }}
							>
								{isEditingStarted ? '编辑中...' : '开始编辑'}
							</button>
						</div>
						<button
							id="editor-mode-btn"
							className={`${isEditMode ? 'active' : ''} ${editStatus === 'processing' ? 'processing' : ''} ${editStatus === 'completed' ? 'completed' : ''}`}
							onClick={() => {
								if (editStatus === 'completed') {
									setShowVersionToggle(true)
									return
								}
								if (editStatus === 'processing') {
									return
								}
								if (isEditMode) {
									exitEditMode()
								}
								setIsEditMode(prev => !prev)
							}}
							type="button"
							style={{ cursor: editStatus === 'processing' ? 'not-allowed' : 'pointer' }}
						>
							{buttonLabel}
						</button>
					</div>
					<button
						type="button"
						className="help-btn"
						onClick={() => setShowHelpModal(true)}
						title="使用指南"
					>
						?
					</button>
				</div>
			</div>

			{/* Help Modal */}
			{showHelpModal && (
				<div className="help-modal-overlay">
					<div className="help-modal">
						<div className="help-modal-header">
							<h2 className="help-modal-title">使用指南</h2>
							<button
								type="button"
								className="help-modal-close"
								onClick={() => setShowHelpModal(false)}
								aria-label="关闭"
							>
								×
							</button>
						</div>
						<div className="help-modal-content">
							{HELP_CONTENT.map((item, index) => (
								<div key={index} className="help-item">
									<div className="help-question">{item.question}</div>
									<div className="help-answer">
										{Array.isArray(item.answer) ? (
											<ul>
												{item.answer.map((line, i) => (
													<li key={i} dangerouslySetInnerHTML={{ __html: line }} />
												))}
											</ul>
										) : (
											<div dangerouslySetInnerHTML={{ __html: item.answer }} />
										)}
									</div>
								</div>
							))}
						</div>
					</div>
				</div>
			)}
		</>
	)
}

export default WebEditor
