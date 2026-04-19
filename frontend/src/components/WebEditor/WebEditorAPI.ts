import Cookies from 'js-cookie'
import { WebEditRequest, WebEditResponse, WebEditStatusResponse, CitationListItem, ModelType } from './types'

const API_BASE_URL = process.env.NODE_ENV === 'production' ? '/api' : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api')

export class WebEditorAPI {
	private isPublic: boolean
	private documentId: number | undefined
	private resourceType: 'web' | 'ppt'
	private slideNumber?: number

	constructor(documentId?: number, isPublic = false, resourceType: 'web' | 'ppt' = 'web', slideNumber?: number) {
		this.documentId = documentId
		this.isPublic = isPublic
		this.resourceType = resourceType
		this.slideNumber = slideNumber
	}

	// Update document ID (used after saving a new version)
	setDocumentId(documentId: number): void {
		this.documentId = documentId
		console.log('[WebEditorAPI] 📝 Document ID updated to:', documentId)
	}

	getDocumentId(): number | undefined {
		return this.documentId
	}

	private getHeaders(includeAuth = false): Record<string, string> {
		const headers: Record<string, string> = {}
		if (includeAuth && !this.isPublic) {
			const token = Cookies.get('access_token')
			if (token) {
				headers['Authorization'] = `Bearer ${token}`
			}
		}
		return headers
	}

	private getStatusEndpoint(): string {
		if (this.resourceType === 'ppt') {
			return this.isPublic ? '/web/public/ppt/edit' : '/web/ppt/edit'
		}
		return '/web/edit'
	}

	private getEditEndpoint(): string {
		if (this.resourceType === 'ppt') {
			return this.isPublic ? '/web/public/ppt/edit' : '/web/ppt/edit'
		}
		return '/web/edit'
	}

	private getKeepVersionEndpoint(
		documentId: number,
		version: 'before' | 'after',
		isPublicRoute = false,
		slideNumber?: number
	): string {
		if (this.resourceType === 'ppt') {
			if (!slideNumber) {
				throw new Error('Slide number is required for PPT editing')
			}
			if (version === 'after') {
				return this.isPublic
					? `${API_BASE_URL}/web/public/ppt/edit/${documentId}/${slideNumber}/save-as-new`
					: `${API_BASE_URL}/web/ppt/edit/${documentId}/${slideNumber}/save-as-new`
			}
			return this.isPublic
				? `${API_BASE_URL}/web/public/ppt/edit/${documentId}/${slideNumber}/keep-version`
				: `${API_BASE_URL}/web/ppt/edit/${documentId}/${slideNumber}/keep-version`
		}
		if (version === 'after') {
			return `${API_BASE_URL}/web/edit/${documentId}/save-as-new`
		}
		return `${API_BASE_URL}/web/edit/${documentId}/keep-version`
	}

	// Submit edit request to backend
	async submitEditRequest(
		docId: number,
		citations: CitationListItem[],
		prompt: string,
		thinkingEnabled?: boolean,
		model?: ModelType
	): Promise<WebEditResponse> {
		const endpoint = this.getEditEndpoint()
		if (this.resourceType === 'ppt' && !this.slideNumber) {
			throw new Error('Slide number is required for PPT editing')
		}

		const citationData = citations.map(c => ({
			id: c.id,
			index: c.index,
			html: c.html,
			selector: c.selector,
			note: c.note
		}))

		const requestBody: WebEditRequest = {
			document_id: docId,
			slide_number: this.resourceType === 'ppt' ? this.slideNumber : undefined,
			citations: citationData,
			user_prompt: prompt,
			thinking_enabled: thinkingEnabled,
			model: model
		}

		console.log('[WebEditorAPI] 📤 发送修改请求到后端:')
		console.log('[WebEditorAPI]   - 端点:', `${API_BASE_URL}${endpoint}`)
		console.log('[WebEditorAPI]   - document_id:', docId)
		console.log('[WebEditorAPI]   - user_prompt:', prompt)
		console.log('[WebEditorAPI]   - thinking_enabled:', thinkingEnabled)
		console.log('[WebEditorAPI]   - model:', model)
		console.log('[WebEditorAPI]   - citations 数量:', citationData.length)

		const headers: Record<string, string> = {
			'Content-Type': 'application/json',
			...this.getHeaders(true)
		}

		const response = await fetch(`${API_BASE_URL}${endpoint}`, {
			method: 'POST',
			headers,
			body: JSON.stringify(requestBody)
		})

		if (!response.ok) {
			throw new Error(`API error: ${response.status}`)
		}

		const result = await response.json()
		console.log('[WebEditorAPI] 📥 后端响应:', result)

		return result
	}

	// Check edit status
	async checkEditStatus(documentId?: number): Promise<WebEditStatusResponse> {
		const docId = documentId || this.documentId
		if (!docId) {
			throw new Error('Document ID is required')
		}
		if (this.resourceType === 'ppt' && !this.slideNumber) {
			throw new Error('Slide number is required for PPT editing')
		}

		const statusEndpoint = this.getStatusEndpoint()
		const statusPath = this.resourceType === 'ppt'
			? `${API_BASE_URL}${statusEndpoint}/${docId}/${this.slideNumber}/status`
			: `${API_BASE_URL}${statusEndpoint}/${docId}/status`

		try {
			const statusResponse = await fetch(
				statusPath,
				{ headers: this.getHeaders(true) }
			)

			if (!statusResponse.ok) {
				throw new Error(`Status check failed: ${statusResponse.status}`)
			}

			const statusResult = await statusResponse.json()
			console.log('[WebEditorAPI] 📊 检查编辑状态:', statusResult.status)

			return statusResult
		} catch (error) {
			console.error('[WebEditorAPI] 检查编辑状态失败:', error)
			throw error
		}
	}

	// Keep version (save as new or replace original)
	async keepVersion(
		documentId: number,
		version: 'before' | 'after',
		isPublicRoute = false,
		slideNumber?: number
	): Promise<{ new_document_id?: number; version_number?: number; root_document_id?: number }> {
		const endpoint = this.getKeepVersionEndpoint(documentId, version, isPublicRoute, slideNumber)

		const requestBody: Record<string, string> = {
			version
		}

		console.log('[WebEditorAPI] 📡 API URL:', endpoint)
		console.log('[WebEditorAPI] 📝 Request body:', requestBody)

		const headers: Record<string, string> = {
			'Content-Type': 'application/json',
			...this.getHeaders(true)
		}

		const response = await fetch(endpoint, {
			method: 'POST',
			headers,
			body: JSON.stringify(requestBody)
		})

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({ detail: '保存失败' }))
			throw new Error(errorData.detail || `HTTP ${response.status}`)
		}

		const result = await response.json()
		console.log('[WebEditorAPI] ✅ Save result:', result)

		return result
	}

	// Get all versions of a document
	async getDocumentVersions(documentId: number): Promise<{
		status: string
		root_document_id: number
		total_versions: number
		max_versions: number
		versions: Array<{
			id: number
			title: string
			version_number: number
			is_current: number
			is_root: boolean
			created_at: string | null
			description: string | null
			user_prompt: string | null
		}>
	}> {
		const endpoint = `${API_BASE_URL}/web/documents/${documentId}/versions`

		console.log('[WebEditorAPI] 📋 Fetching versions for document:', documentId)

		const headers: Record<string, string> = {
			...this.getHeaders(true)
		}

		const response = await fetch(endpoint, { headers })

		if (!response.ok) {
			throw new Error(`Failed to fetch versions: ${response.status}`)
		}

		const result = await response.json()
		console.log('[WebEditorAPI] ✅ Versions result:', result)

		return result
	}

	// Delete a specific version of a document
	async deleteDocumentVersion(documentId: number, versionId: number): Promise<{
		status: string
		message: string
		deleted_version_number: number
	}> {
		const endpoint = `${API_BASE_URL}/web/documents/${documentId}/versions/${versionId}`

		console.log('[WebEditorAPI] 🗑️ Deleting version:', versionId, 'from document:', documentId)

		const headers: Record<string, string> = {
			...this.getHeaders(true)
		}

		const response = await fetch(endpoint, {
			method: 'DELETE',
			headers
		})

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({ detail: '删除失败' }))
			throw new Error(errorData.detail || `HTTP ${response.status}`)
		}

		const result = await response.json()
		console.log('[WebEditorAPI] ✅ Delete result:', result)

		return result
	}
}

// Hook for status streaming (SSE) / polling fallback
export interface StatusPollingOptions {
	documentId: number | undefined
	isPublic: boolean
	resourceType?: 'web' | 'ppt'
	slideNumber?: number
	onProcessing?: () => void
	onCompleted?: (modifiedHtml: string) => void
	onError?: (error: string) => void
	onTimeout?: () => void
	onStatusCheck?: (status: string) => void
	interval?: number
	maxAttempts?: number
}

/**
 * Connect to the backend SSE stream for edit status.
 * Falls back to polling if EventSource is unavailable or the SSE connection fails.
 * Returns a cleanup function (call it to close the connection / stop polling).
 */
export function startStatusPolling(options: StatusPollingOptions): (() => void) | null {
	const {
		documentId,
		isPublic,
		resourceType = 'web',
		slideNumber,
		onProcessing,
		onCompleted,
		onError,
		onTimeout,
		onStatusCheck,
		interval = 5000,
		maxAttempts = 180 // 15 minutes max (for polling fallback)
	} = options

	if (!documentId) return null
	if (resourceType === 'ppt' && !slideNumber) return null

	// --- Build the SSE stream URL ---
	const streamPath = resourceType === 'ppt'
		? (isPublic
			? `/web/public/ppt/edit/${documentId}/${slideNumber}/stream`
			: `/web/ppt/edit/${documentId}/${slideNumber}/stream`)
		: (isPublic
			? `/web/public/edit/${documentId}/stream`
			: `/web/edit/${documentId}/stream`)

	// EventSource cannot send headers; pass JWT as query param for private routes
	let streamUrl = `${API_BASE_URL}${streamPath}`
	if (!isPublic) {
		const token = Cookies.get('access_token')
		if (token) {
			streamUrl += `?token=${encodeURIComponent(token)}`
		}
	}

	// --- Attempt SSE connection ---
	if (typeof EventSource !== 'undefined') {
		let closed = false
		const es = new EventSource(streamUrl)

		es.onmessage = (event) => {
			try {
				const data = JSON.parse(event.data)
				console.log('[WebEditorAPI] 📡 SSE 状态推送:', data.status)
				onStatusCheck?.(data.status)

				if (data.status === 'ready' && data.modified_html) {
					closed = true
					es.close()
					onCompleted?.(data.modified_html)
				} else if (data.status === 'error') {
					closed = true
					es.close()
					onError?.(data.error || '未知错误')
				} else if (data.status === 'timeout') {
					closed = true
					es.close()
					onTimeout?.()
				} else if (data.status === 'processing') {
					onProcessing?.()
				}
			} catch (e) {
				console.error('[WebEditorAPI] SSE 消息解析失败:', e)
			}
		}

		es.onerror = () => {
			if (closed) return
			console.warn('[WebEditorAPI] SSE 连接失败，回退到轮询模式')
			es.close()
			// Fall back to interval polling
			_startPollingFallback(options)
		}

		return () => {
			closed = true
			es.close()
		}
	}

	// --- Fallback: interval polling ---
	return _startPollingFallback(options)
}

/** Internal polling fallback used when SSE is unavailable or errored. */
function _startPollingFallback(options: StatusPollingOptions): (() => void) | null {
	const {
		documentId,
		isPublic,
		resourceType = 'web',
		slideNumber,
		onProcessing,
		onCompleted,
		onError,
		onTimeout,
		onStatusCheck,
		interval = 5000,
		maxAttempts = 180
	} = options

	if (!documentId) return null

	const statusEndpoint = resourceType === 'ppt'
		? (isPublic ? '/web/public/ppt/edit' : '/web/ppt/edit')
		: (isPublic ? '/web/public/edit' : '/web/edit')

	const statusPath = resourceType === 'ppt'
		? `${API_BASE_URL}${statusEndpoint}/${documentId}/${slideNumber}/status`
		: `${API_BASE_URL}${statusEndpoint}/${documentId}/status`

	let attempts = 0

	const pollingInterval = setInterval(async () => {
		attempts++

		try {
			const headers: Record<string, string> = {}
			if (!isPublic) {
				const token = Cookies.get('access_token')
				if (token) headers['Authorization'] = `Bearer ${token}`
			}

			const statusResponse = await fetch(statusPath, { headers })
			if (!statusResponse.ok) return

			const statusResult = await statusResponse.json()
			onStatusCheck?.(statusResult.status)

			if (statusResult.status === 'ready' && statusResult.modified_html) {
				clearInterval(pollingInterval)
				onCompleted?.(statusResult.modified_html)
			} else if (statusResult.status === 'error') {
				clearInterval(pollingInterval)
				onError?.(statusResult.error || '未知错误')
			} else if (attempts >= maxAttempts) {
				clearInterval(pollingInterval)
				onTimeout?.()
			} else if (statusResult.status === 'processing') {
				onProcessing?.()
			}
		} catch (error) {
			console.error('[WebEditorAPI] 轮询状态失败:', error)
		}
	}, interval)

	return () => clearInterval(pollingInterval)
}
