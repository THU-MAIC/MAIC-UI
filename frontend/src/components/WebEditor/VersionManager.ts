import { DocumentVersion, VersionType } from './types'
import { WebEditorAPI } from './WebEditorAPI'

export class VersionManager {
	private documentId: number
	private isPublic: boolean
	private api: WebEditorAPI
	private cachedVersions: DocumentVersion[] = []

	constructor(documentId: number, isPublic = false) {
		this.documentId = documentId
		this.isPublic = isPublic
		this.api = new WebEditorAPI(documentId, isPublic)
	}

	// Fetch versions from backend and cache
	async refreshVersions(): Promise<DocumentVersion[]> {
		try {
			const result = await this.api.getDocumentVersions(this.documentId)
			this.cachedVersions = (result.versions || []).map(version => ({
				id: String(version.id),
				documentId: version.id,
				versionNumber: version.version_number,
				name: version.title,
				modifiedDate: version.created_at || new Date().toISOString(),
				modificationPrompt: version.user_prompt || '无修改指令',
				html: '',
				isCurrent: Number(version.is_current) === 1
			}))
			return this.cachedVersions
		} catch (error) {
			console.error('[VersionManager] Error retrieving versions from backend:', error)
			return this.cachedVersions
		}
	}

	// Get cached versions
	getStoredVersions(): DocumentVersion[] {
		return this.cachedVersions
	}

	// Save versions to cache
	storeVersions(versions: DocumentVersion[]): void {
		this.cachedVersions = versions
	}

	// Add a new version
	addVersion(
		versionType: VersionType,
		html: string,
		modificationPrompt: string,
		makeCurrent = false,
		versionNumber?: number
	): DocumentVersion {
		const versionName = versionType === 'before' ? '修改前' : '修改后'
		const newVersion: DocumentVersion = {
			id: `version_${Date.now()}_${this.documentId}`,
			documentId: this.documentId,
			versionNumber,
			name: `${versionName} - ${new Date().toLocaleString('zh-CN')}`,
			modifiedDate: new Date().toISOString(),
			modificationPrompt,
			html,
			isCurrent: makeCurrent
		}

		const existingVersions = this.getStoredVersions()
		const updatedVersions = makeCurrent
			? [newVersion, ...existingVersions.filter(v => !v.isCurrent)]
			: [newVersion, ...existingVersions.filter(v => !v.isCurrent)]
		this.storeVersions(updatedVersions)

		return newVersion
	}

	// Keep a specific version (replace or save as new)
	async keepVersion(
		versionType: VersionType,
		htmlToSave: string,
		modificationPrompt: string,
		apiCall: () => Promise<{ new_document_id?: number; version_number?: number; root_document_id?: number }>,
		isPublicRoute = false
	): Promise<{ newDocumentId?: number; versionNumber?: number; rootDocumentId?: number }> {
		try {
			// Call API to keep version
			const result = await apiCall()
			await this.refreshVersions()

			console.log('[VersionManager] 🎉 Version saved successfully')
			console.log('[VersionManager] 📊 Version info:', {
				newDocumentId: result.new_document_id,
				versionNumber: result.version_number,
				rootDocumentId: result.root_document_id
			})

			return {
				newDocumentId: result.new_document_id,
				versionNumber: result.version_number,
				rootDocumentId: result.root_document_id
			}
		} catch (error) {
			console.error('[VersionManager] ❌ Save version error:', error)
			throw error
		}
	}

	// Get current version
	getCurrentVersion(): DocumentVersion | null {
		const versions = this.getStoredVersions()
		return versions.find(v => v.isCurrent) || null
	}

	// Set current version
	setCurrentVersion(versionId: string): void {
		const versions = this.getStoredVersions()
		const updatedVersions = versions.map(v => ({
			...v,
			isCurrent: v.id === versionId
		}))
		this.storeVersions(updatedVersions)
	}

	// Delete a version
	async deleteVersion(versionId: string): Promise<void> {
		const parsedId = Number(versionId)
		if (Number.isNaN(parsedId)) {
			console.warn('[VersionManager] Invalid version id:', versionId)
			return
		}
		try {
			await this.api.deleteDocumentVersion(this.documentId, parsedId)
			await this.refreshVersions()
		} catch (error) {
			console.error('[VersionManager] Error deleting version:', error)
		}
	}

	// Clear all versions
	clearAllVersions(): void {
		this.cachedVersions = []
	}

	// Get version by ID
	getVersionById(versionId: string): DocumentVersion | null {
		const versions = this.getStoredVersions()
		return versions.find(v => v.id === versionId) || null
	}
}
