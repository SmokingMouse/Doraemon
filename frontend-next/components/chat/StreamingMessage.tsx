'use client';

import { MarkdownContent } from './MarkdownContent';

export function StreamingMessage({ content }: { content: string }) {
  if (!content) return null;

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[70%] rounded-lg px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 shadow-sm">
        <div className="relative">
          <MarkdownContent content={content} />
          <span className="inline-block w-2 h-4 ml-1 bg-gray-400 dark:bg-gray-500 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
