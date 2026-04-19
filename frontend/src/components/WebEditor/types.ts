export interface DocumentVersion {
	id: string
	documentId: number
	versionNumber?: number
	name: string
	modifiedDate: string
	modificationPrompt: string
	html: string
	isCurrent: boolean
	isRoot?: boolean
}

export interface WebEditorProps {
	targetIframeRef?: React.RefObject<HTMLIFrameElement>
	documentId?: number
	isPublic?: boolean
	resourceType?: 'web' | 'ppt'
	slideNumber?: number
	onEditStatusChange?: (status: 'idle' | 'processing' | 'completed') => void
	onEditModeChange?: (isEditMode: boolean) => void
	onVersionSaved?: (version?: DocumentVersion) => void
}

export type EditStatus = 'idle' | 'processing' | 'completed'
export type VersionType = 'before' | 'after'
export type ModelType = 'claude-sonnet-4-6' | 'claude-opus-4-6' | 'claude-haiku-4-5-20251001' | 'glm-4.7' | 'glm-4.6'

export const MODEL_OPTIONS: ReadonlyArray<{ label: string; value: ModelType }> = [
	{ label: 'Claude Sonnet 4.6', value: 'claude-sonnet-4-6' },
	{ label: 'Claude Opus 4.6', value: 'claude-opus-4-6' },
	{ label: 'Claude Haiku 4.5', value: 'claude-haiku-4-5-20251001' },
	{ label: 'GLM 4.7', value: 'glm-4.7' },
	{ label: 'GLM 4.6', value: 'glm-4.6' }
]

export const MODEL_LABEL_TO_TYPE: Record<string, ModelType> = {
	'Claude Sonnet 4.6': 'claude-sonnet-4-6',
	'Claude Opus 4.6': 'claude-opus-4-6',
	'Claude Haiku 4.5': 'claude-haiku-4-5-20251001',
	'GLM 4.7': 'glm-4.7',
	'GLM 4.6': 'glm-4.6'
}

export const MODEL_TYPE_TO_LABEL: Record<ModelType, string> = {
	'claude-sonnet-4-6': 'Claude Sonnet 4.6',
	'claude-opus-4-6': 'Claude Opus 4.6',
	'claude-haiku-4-5-20251001': 'Claude Haiku 4.5',
	'glm-4.7': 'GLM 4.7',
	'glm-4.6': 'GLM 4.6'
}

export interface HighlightContext {
	doc: Document
	iframe: HTMLIFrameElement | null
}

export interface CitationListItem {
	id: number
	index: number
	html: string
	selector: string
	note?: string
	pageBadge?: HTMLDivElement
	highlightOverlay?: HTMLDivElement
	element?: Element
	context?: HighlightContext
}

export type CitationListNode = {
	value: CitationListItem
	next: CitationListNode | null
}

export interface EditorConfig {
	buttonPosition: string
	highlightColor: string
	copyNotification: boolean
	disableAnimations: boolean
	excludeSelectors: string[]
}

export interface WebEditRequest {
	document_id: number
	slide_number?: number
	citations: Array<{
		id: number
		index: number
		html: string
		selector: string
		note?: string
	}>
	user_prompt: string
	thinking_enabled?: boolean
	model?: ModelType
}

export interface WebEditStatusResponse {
	status: 'not_started' | 'processing' | 'ready' | 'error'
	modified_html?: string
	error?: string
}

export interface WebEditResponse {
	status: 'processing' | 'success'
}
