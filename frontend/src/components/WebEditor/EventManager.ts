import { HighlightContext } from './types'
import { DOMHighlighter } from './DOMHighlighter'
import { CitationListManager } from './CitationListManager'

export class EventManager {
	private iframeRegistry: WeakMap<HTMLIFrameElement, Record<string, EventListener>>
	private mainHandlers: Record<string, EventListener> | null
	private highlighter: DOMHighlighter
	private citationListManager: CitationListManager
	private iframeObserver: MutationObserver | null
	private targetIframeRef: React.RefObject<HTMLIFrameElement> | undefined
	private isEditMode: boolean
	private onCitationAdd?: (element: Element, context: HighlightContext) => void
	private setEditMode?: (value: boolean) => void

	constructor(
		highlighter: DOMHighlighter,
		citationListManager: CitationListManager,
		targetIframeRef?: React.RefObject<HTMLIFrameElement>
	) {
		this.iframeRegistry = new WeakMap()
		this.mainHandlers = null
		this.highlighter = highlighter
		this.citationListManager = citationListManager
		this.iframeObserver = null
		this.targetIframeRef = targetIframeRef
		this.isEditMode = false
	}

	setEditModeState(isEditMode: boolean, setEditMode?: (value: boolean) => void): void {
		this.isEditMode = isEditMode
		this.setEditMode = setEditMode
	}

	setOnCitationAdd(callback: (element: Element, context: HighlightContext) => void): void {
		this.onCitationAdd = callback
	}

	// Attach event listeners to a document
	attachDocumentListeners(doc: Document, iframeEl: HTMLIFrameElement | null): void {
		const handlers: Record<string, EventListener> = {
			mousemove: (e: Event) => this.handleMouseMove(e as MouseEvent, doc, iframeEl),
			click: (e: Event) => this.handleClick(e as MouseEvent, doc, iframeEl),
			keydown: (e: Event) => {
				if ((e as KeyboardEvent).key === 'Escape' && this.isEditMode) {
					this.setEditMode?.(false)
				}
			}
		}

		doc.addEventListener('mousemove', handlers.mousemove, true)
		doc.addEventListener('click', handlers.click, true)
		doc.addEventListener('keydown', handlers.keydown, true)

		if (iframeEl) {
			this.iframeRegistry.set(iframeEl, handlers)
		} else {
			this.mainHandlers = handlers
		}
	}

	// Detach event listeners from a document
	detachDocumentListeners(doc: Document, iframeEl: HTMLIFrameElement | null): void {
		if (iframeEl) {
			const handlers = this.iframeRegistry.get(iframeEl)
			if (handlers) {
				doc.removeEventListener('mousemove', handlers.mousemove, true)
				doc.removeEventListener('click', handlers.click, true)
				doc.removeEventListener('keydown', handlers.keydown, true)
				this.iframeRegistry.delete(iframeEl)
			}
			return
		}

		if (this.mainHandlers) {
			doc.removeEventListener('mousemove', this.mainHandlers.mousemove, true)
			doc.removeEventListener('click', this.mainHandlers.click, true)
			doc.removeEventListener('keydown', this.mainHandlers.keydown, true)
			this.mainHandlers = null
		}
	}

	// Handle mouse move
	private handleMouseMove(e: MouseEvent, doc: Document, iframeEl: HTMLIFrameElement | null): void {
		this.highlighter.handleMouseMove(e, doc, iframeEl, this.isEditMode)
	}

	// Handle click
	private handleClick(e: MouseEvent, doc: Document, iframeEl: HTMLIFrameElement | null): void {
		if (!this.isEditMode) return

		const selectedElement = this.highlighter.selectedElement
		if (!selectedElement || this.highlighter.shouldExcludeElement(selectedElement)) return
		if (doc === document && this.highlighter.isEditorUiTarget(e.target)) return

		e.preventDefault()
		e.stopPropagation()
		e.stopImmediatePropagation()

		const elementHTML = (selectedElement as HTMLElement).outerHTML
		const index = this.citationListManager.getLength() + 1

		const context: HighlightContext = { doc, iframe: iframeEl }

		const highlightOverlay = this.highlighter.createPinnedOverlay()
		this.highlighter.pinHighlight(selectedElement, context, highlightOverlay)
		const pageBadge = this.highlighter.addNumberBadge(selectedElement, context, index)

		this.citationListManager.append({
			index,
			html: elementHTML,
			selector: this.highlighter.generateSelector(selectedElement),
			pageBadge,
			highlightOverlay,
			element: selectedElement,
			context
		})

		this.onCitationAdd?.(selectedElement, context)
	}

	// Register iframe listeners
	registerIframe(iframe: HTMLIFrameElement): void {
		if (this.iframeRegistry.has(iframe)) return

		const tryAttach = () => {
			try {
				if (!iframe.contentDocument) return
				this.attachDocumentListeners(iframe.contentDocument, iframe)
			} catch (_) {
				// ignore cross-origin iframes
			}
		}

		if (iframe.contentDocument && iframe.contentDocument.readyState !== 'loading') {
			tryAttach()
		} else {
			iframe.addEventListener('load', tryAttach, { once: true })
		}
	}

	// Register all iframes
	registerIframes(): void {
		const iframeList = this.targetIframeRef?.current
			? [this.targetIframeRef.current]
			: Array.from(document.querySelectorAll('iframe'))
		iframeList.forEach(iframe => this.registerIframe(iframe))

		if (!this.iframeObserver) {
			this.iframeObserver = new MutationObserver(() => {
				if (!this.isEditMode) return
				const nextList = this.targetIframeRef?.current
					? [this.targetIframeRef.current]
					: Array.from(document.querySelectorAll('iframe'))
				nextList.forEach(iframe => this.registerIframe(iframe))
			})
			this.iframeObserver.observe(document.documentElement, { childList: true, subtree: true })
		}
	}

	// Unregister all iframes
	unregisterIframes(): void {
		const iframeList = this.targetIframeRef?.current
			? [this.targetIframeRef.current]
			: Array.from(document.querySelectorAll('iframe'))

		iframeList.forEach(iframe => {
			try {
				if (iframe.contentDocument) {
					this.detachDocumentListeners(iframe.contentDocument, iframe)
				}
			} catch (_) {
				// ignore cross-origin iframes
			}
		})

		if (this.iframeObserver) {
			this.iframeObserver.disconnect()
			this.iframeObserver = null
		}
	}

	// Cleanup
	cleanup(): void {
		this.unregisterIframes()
		this.detachDocumentListeners(document, null)
	}
}
