'use client';

import { useParams } from 'next/navigation';
import PPTTemplateSelection from '../../../../components/templates/PPTTemplateSelection';
import { useRouter } from 'next/navigation';

export default function PPTTemplateSelectionPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = parseInt(params.documentId as string);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <PPTTemplateSelection
        documentId={documentId}
        onCompleted={() => router.push(`/ppt-viewer/${documentId}`)}
      />
    </div>
  );
}
