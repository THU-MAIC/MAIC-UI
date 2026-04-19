import { HighlightContext, CitationListItem, EditorConfig } from './types'

const config: EditorConfig = {
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

// Styles to inject into iframe for highlight elements
const IFRAME_STYLES = `
.element-highlight-overlay {
	position: absolute;
	pointer-events: none;
	z-index: 999998;
	border: 2px solid #f00;
	background-color: rgba(255, 0, 0, 0.1);
	transition: all 0.2s ease;
}
.editor-number-badge {
	position: absolute;
	width: 28px;
	height: 28px;
	border-radius: 50%;
	background: #f5576c;
	color: #fff;
	font-size: 13px;
	font-weight: bold;
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1000000;
	pointer-events: none;
	box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}
`

export class DOMHighlighter {
	private selectedElementRef: { current: Element | null }
	private highlightOverlayRef: { current: HTMLDivElement | null }
	private numberBadgesRef: { current: HTMLDivElement[] }
	private clickCounterRef: { current: number }
	private tooltipRef: { current: HTMLDivElement | null }
	private modeIndicatorRef: { current: HTMLDivElement | null }
	private targetIframeRef: React.RefObject<HTMLIFrameElement> | null
	private stylesInjected: boolean

	constructor() {
		this.selectedElementRef = { current: null }
		this.highlightOverlayRef = { current: null }
		this.numberBadgesRef = { current: [] }
		this.clickCounterRef = { current: 0 }
		this.tooltipRef = { current: null }
		this.modeIndicatorRef = { current: null }
		this.targetIframeRef = null
		this.stylesInjected = false
	}

	setTargetIframe(ref: React.RefObject<HTMLIFrameElement> | null): void {
		this.targetIframeRef = ref
		// Reset all internal state when iframe changes (content may be replaced)
		this.stylesInjected = false
		this.highlightOverlayRef.current = null
		this.numberBadgesRef.current = []
	}

	// Call this when iframe content is replaced (e.g., after saving a new version)
	invalidateIframeContent(): void {
		this.stylesInjected = false
		this.highlightOverlayRef.current = null
		this.numberBadgesRef.current = []
		this.clickCounterRef.current = 0
	}

	private getTargetDocument(): Document | null {
		return this.targetIframeRef?.current?.contentDocument || null
	}

	private injectStylesIntoIframe(): void {
		const targetDoc = this.getTargetDocument()
		if (!targetDoc) return

		// Always verify if styles still exist in the document (may be removed after iframe reload)
		const existingStyle = targetDoc.getElementById('editor-highlight-styles')
		if (existingStyle) {
			this.stylesInjected = true
			return
		}

		// Styles don't exist (either never injected or document was replaced)
		this.stylesInjected = false
		const style = targetDoc.createElement('style')
		style.id = 'editor-highlight-styles'
		style.textContent = IFRAME_STYLES
		targetDoc.head.appendChild(style)
		this.stylesInjected = true
	}

	// Get editable documents (main document and iframe documents)
	getEditableDocuments(targetIframeRef?: React.RefObject<HTMLIFrameElement>): Document[] {
		const targetDoc = targetIframeRef?.current?.contentDocument || null
		return targetDoc ? [targetDoc] : []
	}

	shouldExcludeElement(element: Element): boolean {
		return config.excludeSelectors.some(selector => element.matches(selector))
	}

	isEditorUiTarget(target: EventTarget | null): boolean {
		if (!(target instanceof HTMLElement)) return false
		return Boolean(
			target.closest('#editor-mode-container') ||
			target.closest('.version-toggle-container')
		)
	}

	// Highlight overlay management
	createHighlightOverlay(): void {
		const targetDoc = this.getTargetDocument()
		if (!targetDoc) return

		this.injectStylesIntoIframe()

		// Validate existing overlay - check if it's still in the document
		// (may be removed after iframe content reload)
		if (this.highlightOverlayRef.current) {
			if (!targetDoc.body.contains(this.highlightOverlayRef.current)) {
				// Overlay was removed (e.g., iframe content was replaced)
				this.highlightOverlayRef.current = null
			}
		}

		if (!this.highlightOverlayRef.current) {
			const overlay = targetDoc.createElement('div')
			overlay.className = 'element-highlight-overlay'
			overlay.style.display = 'none'
			targetDoc.body.appendChild(overlay)
			this.highlightOverlayRef.current = overlay
		}
	}

	removeHighlightOverlay(): void {
		if (this.highlightOverlayRef.current) {
			this.highlightOverlayRef.current.remove()
			this.highlightOverlayRef.current = null
		}
	}

	createPinnedOverlay(): HTMLDivElement {
		const targetDoc = this.getTargetDocument()
		// Fallback to main document if no iframe (shouldn't happen normally)
		const doc = targetDoc || document

		this.injectStylesIntoIframe()

		const pinned = doc.createElement('div')
		pinned.className = 'element-highlight-overlay'
		pinned.style.display = 'none'
		doc.body.appendChild(pinned)
		return pinned
	}

	// Mode indicator
	createModeIndicator(): void {
		if (document.getElementById('editor-mode-indicator')) return
		const indicator = document.createElement('div')
		indicator.className = 'mode-indicator'
		indicator.textContent = '编辑模式 (ESC退出)'
		indicator.id = 'editor-mode-indicator'
		document.body.appendChild(indicator)
		this.modeIndicatorRef.current = indicator
	}

	removeModeIndicator(): void {
		const indicator = document.getElementById('editor-mode-indicator')
		if (indicator) indicator.remove()
	}

	// Tooltip management
	private getOrCreateTooltip(): HTMLDivElement {
		let tooltip = this.tooltipRef.current
		if (!tooltip) {
			tooltip = document.querySelector('.editor-tooltip') as HTMLDivElement | null
			if (!tooltip) {
				tooltip = document.createElement('div')
				tooltip.className = 'editor-tooltip'
				document.body.appendChild(tooltip)
			}
			this.tooltipRef.current = tooltip
		}
		return tooltip
	}

	showTooltip(rect: DOMRect, iframeOffset: DOMRect, text: string): void {
		const tooltip = this.getOrCreateTooltip()
		tooltip.textContent = text
		tooltip.style.display = 'block'

		const offsetLeft = rect.left + iframeOffset.left + (window.pageXOffset || document.documentElement.scrollLeft)
		const offsetTop = rect.top + iframeOffset.top + (window.pageYOffset || document.documentElement.scrollTop)
		const rectBottom = offsetTop + rect.height
		const tooltipRect = tooltip.getBoundingClientRect()
		const scrollTop = window.pageYOffset || document.documentElement.scrollTop
		const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft

		const aboveTop = offsetTop - tooltipRect.height - 8
		const belowTop = rectBottom + 8
		const viewportTop = scrollTop

		const top = aboveTop >= viewportTop ? aboveTop : belowTop
		let left = offsetLeft

		const maxLeft = scrollLeft + window.innerWidth - tooltipRect.width - 8
		if (left > maxLeft) left = maxLeft
		if (left < scrollLeft + 8) left = scrollLeft + 8

		tooltip.style.left = `${left}px`
		tooltip.style.top = `${top}px`
	}

	hideTooltip(): void {
		const tooltip = this.tooltipRef.current
		if (tooltip) tooltip.style.display = 'none'
	}

	removeTooltip(): void {
		const tooltip = this.tooltipRef.current
		if (tooltip) {
			tooltip.remove()
			this.tooltipRef.current = null
		}
	}

	// Positioning helpers - now positions within iframe document
	private positionOverlayInIframe(
		overlay: HTMLDivElement,
		rect: DOMRect,
		scrollLeft: number,
		scrollTop: number
	): void {
		overlay.style.display = 'block'
		overlay.style.left = `${rect.left + scrollLeft}px`
		overlay.style.top = `${rect.top + scrollTop}px`
		overlay.style.width = `${rect.width}px`
		overlay.style.height = `${rect.height}px`
	}

	highlightElement(element: Element, context: HighlightContext): void {
		const overlay = this.highlightOverlayRef.current
		if (!overlay) return

		const rect = element.getBoundingClientRect()
		// Use iframe's scroll position since overlay is now inside iframe
		const targetDoc = context.doc
		const scrollTop = targetDoc.documentElement.scrollTop || targetDoc.body.scrollTop || 0
		const scrollLeft = targetDoc.documentElement.scrollLeft || targetDoc.body.scrollLeft || 0

		this.positionOverlayInIframe(overlay, rect, scrollLeft, scrollTop)

		// Tooltip still needs iframe offset as it's in the main document
		const iframeOffset = context.iframe ? context.iframe.getBoundingClientRect() : new DOMRect(0, 0, 0, 0)
		const tagName = element.tagName.toLowerCase()
		const id = (element as HTMLElement).id ? `#${(element as HTMLElement).id}` : ''
		const className = (element as HTMLElement).className
		const classes = className && typeof className === 'string'
			? `.${className.trim().split(/\s+/).filter(Boolean).join('.')}`
			: ''
			const styleAttr = (element as HTMLElement).getAttribute('style')?.trim() || ''
		const rawContent = (element.textContent || '').replace(/\s+/g, ' ').trim()
		const truncatedContent = rawContent.length > 50 ? `${rawContent.slice(0, 50)}...` : rawContent
		const tooltipParts = [`${tagName}${id}${classes}`]
		if (styleAttr) tooltipParts.push(`${styleAttr}`)
		if (truncatedContent) tooltipParts.push(`${truncatedContent}`)
		this.showTooltip(rect, iframeOffset, tooltipParts.join('\n'))
	}

	addNumberBadge(element: Element, context: HighlightContext, index: number): HTMLDivElement {
		const rect = element.getBoundingClientRect()
		// Use iframe's scroll position since badge is now inside iframe
		const targetDoc = context.doc
		const scrollTop = targetDoc.documentElement.scrollTop || targetDoc.body.scrollTop || 0
		const scrollLeft = targetDoc.documentElement.scrollLeft || targetDoc.body.scrollLeft || 0

		const doc = this.getTargetDocument() || document
		this.injectStylesIntoIframe()

		const badge = doc.createElement('div')
		badge.className = 'editor-number-badge'
		badge.textContent = String(index)

		const centerX = rect.left + rect.width / 2 + scrollLeft
		const centerY = rect.top + rect.height / 2 + scrollTop
		badge.style.left = `${centerX - 14}px`
		badge.style.top = `${centerY - 14}px`

		doc.body.appendChild(badge)
		this.numberBadgesRef.current.push(badge)
		return badge
	}

	resetNumberBadges(): void {
		this.numberBadgesRef.current.forEach(badge => badge.remove())
		this.numberBadgesRef.current = []
		this.clickCounterRef.current = 0
	}

	pinHighlight(element: Element, context: HighlightContext, overlay: HTMLDivElement): void {
		const rect = element.getBoundingClientRect()
		// Use iframe's scroll position since overlay is now inside iframe
		const targetDoc = context.doc
		const scrollTop = targetDoc.documentElement.scrollTop || targetDoc.body.scrollTop || 0
		const scrollLeft = targetDoc.documentElement.scrollLeft || targetDoc.body.scrollLeft || 0

		this.positionOverlayInIframe(overlay, rect, scrollLeft, scrollTop)
	}

	// Notification
	showNotification(message: string): void {
		if (!config.copyNotification) return
		const notification = document.createElement('div')
		notification.style.cssText = `
			position: fixed;
			top: 20px;
			right: 20px;
			background: #4CAF50;
			color: white;
			padding: 12px 24px;
			border-radius: 6px;
			z-index: 1000001;
			animation: slideIn 0.3s ease;
		`
		notification.textContent = message
		document.body.appendChild(notification)

		setTimeout(() => {
			notification.style.animation = 'slideOut 0.3s ease'
			setTimeout(() => notification.remove(), 300)
		}, 2000)
	}

	// Generate CSS selector
	generateSelector(element: Element): string {
		const elementId = (element as HTMLElement).id
		if (elementId) {
			return `#${elementId}`
		}

		const path: string[] = []
		let current: Element | null = element
		while (current && current.nodeType === Node.ELEMENT_NODE) {
			let selector = current.nodeName.toLowerCase()
			const className = (current as HTMLElement).className
			if (className && typeof className === 'string') {
				const classes = className.trim().split(/\s+/)
				if (classes.length > 0) {
					selector += `.${classes.join('.')}`
				}
			}

			if (!(current as HTMLElement).id) {
				let sibling: Element | null = current
				let nth = 1
				while ((sibling = sibling.previousElementSibling)) {
					if (sibling.nodeName.toLowerCase() === selector) nth += 1
				}
				if (nth !== 1) {
					selector += `:nth-of-type(${nth})`
				}
			}

			path.unshift(selector)

			if ((current as HTMLElement).id) break
			current = current.parentElement
		}

		return path.join(' > ') || '*'
	}

	// Navigation prevention
	preventLinkNavigation(e: Event): void {
		e.preventDefault()
		e.stopPropagation()
	}

	preventFormSubmit(e: Event): void {
		e.preventDefault()
		e.stopPropagation()
	}

	preventNavigation(e: Event): void {
		const target = e.target as HTMLElement | null
		if (target?.closest('#editor-mode-container')) return
		if (target?.tagName === 'A' || target?.closest('a')) {
			e.preventDefault()
			e.stopPropagation()
		}
	}

	// Dynamic elements management
	disableDynamicElements(targetIframeRef?: React.RefObject<HTMLIFrameElement>): void {
		const docs = this.getEditableDocuments(targetIframeRef)
		docs.forEach(doc => {
			doc.querySelectorAll('*').forEach(element => {
				if (this.shouldExcludeElement(element)) return
				if ((element as HTMLElement).tagName === 'A') {
					element.addEventListener('click', this.preventLinkNavigation.bind(this))
				}
			})

			doc.querySelectorAll('form').forEach(form => {
				form.addEventListener('submit', this.preventFormSubmit.bind(this))
			})

			doc.addEventListener('click', this.preventNavigation.bind(this), true)
		})
	}

	restoreDynamicElements(targetIframeRef?: React.RefObject<HTMLIFrameElement>): void {
		const docs = this.getEditableDocuments(targetIframeRef)
		docs.forEach(doc => {
			doc.querySelectorAll('form').forEach(form => {
				form.removeEventListener('submit', this.preventFormSubmit.bind(this))
			})
			doc.removeEventListener('click', this.preventNavigation.bind(this), true)
		})
	}

	// Event handlers
	handleMouseMove(
		e: MouseEvent,
		doc: Document,
		iframeEl: HTMLIFrameElement | null,
		isEditMode: boolean
	): void {
		if (!isEditMode) return

		// Check if mouse is over editor UI area first - hide highlight if so
		if (this.isEditorUiTarget(e.target)) {
			this.selectedElementRef.current = null
			if (this.highlightOverlayRef.current) {
				this.highlightOverlayRef.current.style.display = 'none'
			}
			this.hideTooltip()
			return
		}

		if (doc === document) return
		e.stopPropagation()

		const element = doc.elementFromPoint(e.clientX, e.clientY)
		if (element && element !== doc.documentElement && element !== doc.body) {
			this.selectedElementRef.current = element
			this.highlightElement(element, { doc, iframe: iframeEl })
		} else {
			this.selectedElementRef.current = null
			if (this.highlightOverlayRef.current) {
				this.highlightOverlayRef.current.style.display = 'none'
			}
			this.hideTooltip()
		}
	}

	// Citation list management
	clearCitationArtifacts(head: { value: CitationListItem; next: any } | null): void {
		let current = head
		while (current) {
			current.value.pageBadge?.remove()
			current.value.highlightOverlay?.remove()
			current = current.next
		}
		this.numberBadgesRef.current = []
	}

	// Update pinned positions on scroll
	updatePinnedPositions(head: { value: CitationListItem; next: any } | null): void {
		let current = head
		while (current) {
			const item = current.value
			if (item.element && item.context) {
				const rect = item.element.getBoundingClientRect()
				// Use iframe's scroll position since overlays and badges are now inside iframe
				const targetDoc = item.context.doc
				const scrollTop = targetDoc.documentElement.scrollTop || targetDoc.body.scrollTop || 0
				const scrollLeft = targetDoc.documentElement.scrollLeft || targetDoc.body.scrollLeft || 0

				if (item.highlightOverlay) {
					item.highlightOverlay.style.left = `${rect.left + scrollLeft}px`
					item.highlightOverlay.style.top = `${rect.top + scrollTop}px`
					item.highlightOverlay.style.width = `${rect.width}px`
					item.highlightOverlay.style.height = `${rect.height}px`
				}

				if (item.pageBadge) {
					const centerX = rect.left + rect.width / 2 + scrollLeft
					const centerY = rect.top + rect.height / 2 + scrollTop
					item.pageBadge.style.left = `${centerX - 14}px`
					item.pageBadge.style.top = `${centerY - 14}px`
				}
			}
			current = current.next
		}
	}

	// Getters
	get selectedElement(): Element | null {
		return this.selectedElementRef.current
	}

	set selectedElement(element: Element | null) {
		this.selectedElementRef.current = element
	}

	get highlightOverlay(): HTMLDivElement | null {
		return this.highlightOverlayRef.current
	}

	// Cleanup
	cleanup(): void {
		this.removeHighlightOverlay()
		this.removeTooltip()
		this.removeModeIndicator()
		this.resetNumberBadges()
		this.removeInjectedStyles()
	}

	private removeInjectedStyles(): void {
		const targetDoc = this.getTargetDocument()
		if (targetDoc) {
			const style = targetDoc.getElementById('editor-highlight-styles')
			if (style) style.remove()
		}
		this.stylesInjected = false
	}
}
