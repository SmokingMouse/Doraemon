'use client';

export function StreamingMessage({ content }: { content: string }) {
  if (!content) return null;

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[70%] rounded-lg px-4 py-3 bg-white border border-gray-200 text-gray-800">
        <div className="whitespace-pre-wrap break-words">
          {content}
          <span className="inline-block w-2 h-4 ml-1 bg-gray-400 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
