import { CitationListItem, CitationListNode } from './types'

export class CitationListManager {
	private head: CitationListNode | null
	private tail: CitationListNode | null
	private length: number
	private nextId: number

	constructor() {
		this.head = null
		this.tail = null
		this.length = 0
		this.nextId = 1
	}

	// Append a citation to the list
	append(item: Omit<CitationListItem, 'id'>): number {
		const id = this.nextId++
		const newItem: CitationListItem = { ...item, id }
		const node: CitationListNode = { value: newItem, next: null }

		if (!this.head) {
			this.head = node
			this.tail = node
		} else if (this.tail) {
			this.tail.next = node
			this.tail = node
		}

		this.length++
		return id
	}

	// Remove a citation by ID
	remove(id: number): CitationListItem | null {
		let current = this.head
		let prev: CitationListNode | null = null
		let removedItem: CitationListItem | null = null

		while (current) {
			if (current.value.id === id) {
				removedItem = current.value

				if (prev) {
					prev.next = current.next
				} else {
					this.head = current.next
				}

				if (this.tail === current) {
					this.tail = prev
				}

				this.length--
				break
			}
			prev = current
			current = current.next
		}

		if (removedItem) {
			this.renumber()
		}

		return removedItem
	}

	// Get all citations as array
	getAll(): CitationListItem[] {
		const items: CitationListItem[] = []
		let current = this.head
		while (current) {
			items.push(current.value)
			current = current.next
		}
		return items
	}

	// Get the head node
	getHead(): CitationListNode | null {
		return this.head
	}

	// Get the length
	getLength(): number {
		return this.length
	}

	// Renumber all citations
	private renumber(): void {
		let current = this.head
		let index = 1
		while (current) {
			current.value.index = index
			if (current.value.pageBadge) {
				current.value.pageBadge.textContent = String(index)
			}
			index++
			current = current.next
		}
	}

	// Clear all citations
	clear(): void {
		this.head = null
		this.tail = null
		this.length = 0
	}

	// Get next ID
	getNextId(): number {
		return this.nextId
	}

	// Find citation by ID
	findById(id: number): CitationListItem | null {
		let current = this.head
		while (current) {
			if (current.value.id === id) {
				return current.value
			}
			current = current.next
		}
		return null
	}
}
