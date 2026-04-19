import React from 'react'
import { Button } from '@/components/ui/Button'
import { DocumentVersion } from '@/components/WebEditor'

export interface VersionListProps {
	versions: DocumentVersion[]
	onApplyVersion: (version: DocumentVersion) => void
	onDeleteVersion: (version: DocumentVersion) => void
	className?: string
	label?: string
}

const formatDate = (dateString: string) => {
	const date = new Date(dateString)
	return date.toLocaleString('zh-CN', {
		year: 'numeric',
		month: '2-digit',
		day: '2-digit',
		hour: '2-digit',
		minute: '2-digit'
	})
}

export function VersionList({
	versions,
	onApplyVersion,
	onDeleteVersion,
	className,
	label = '可交互文件版本'
}: VersionListProps) {
	if (!versions.length) {
		return null
	}

	const sortedVersions = [...versions].sort((a, b) => {
		if (a.isCurrent && !b.isCurrent) return -1
		if (!a.isCurrent && b.isCurrent) return 1
		const aVersion = a.versionNumber ?? 0
		const bVersion = b.versionNumber ?? 0
		return aVersion - bVersion
	})

	return (
		<div className={`bg-white rounded-lg shadow p-6 ${className || ''}`.trim()}>
			<h2 className="text-xl font-semibold text-gray-900 mb-4">{label}</h2>
			<div className="overflow-x-auto">
				<table className="min-w-full divide-y divide-gray-200">
					<thead className="bg-gray-50">
						<tr>
							<th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">版本</th>
							<th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">修改日期</th>
							<th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">修改指令</th>
							<th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
						</tr>
					</thead>
					<tbody className="divide-y divide-gray-200 bg-white">
						{sortedVersions.map((version) => (
							<tr
								key={version.id}
								className={version.isCurrent ? 'bg-green-50' : 'bg-white'}
							>
								<td className="px-4 py-3 text-sm font-semibold text-gray-900">
									<div className="flex items-center gap-2">
										<span>{`v${version.versionNumber ?? '-'}`}</span>
										{version.isCurrent && (
											<span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
												当前使用
											</span>
										)}
									</div>
								</td>
								<td className="px-4 py-3 text-sm text-gray-600">{formatDate(version.modifiedDate)}</td>
								<td className="px-4 py-3 text-sm text-gray-600">
									<div className="truncate max-w-[360px]" title={version.modificationPrompt}>
										{version.modificationPrompt}
									</div>
								</td>
								<td className="px-4 py-3 text-right">
									{!version.isCurrent && (
										<div className="flex items-center justify-end gap-2">
											<Button
												onClick={() => onApplyVersion(version)}
												className="px-4 py-2 text-sm"
											>
												应用
											</Button>
											{/* <Button
												onClick={() => onDeleteVersion(version)}
												className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 disabled:bg-red-300 disabled:cursor-not-allowed"
												disabled={Boolean(version.isRoot)}
												title={version.isRoot ? '初始版本不可删除' : '删除'}
											>
												删除
											</Button> */}
										</div>
									)}
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	)
}
