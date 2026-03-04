'use client';

import { useState } from 'react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onCommand: (command: string) => void;
}

const COMMANDS = [
  { name: '/new', description: '创建新会话' },
  { name: '/clear', description: '清空当前会话上下文' },
  { name: '/thinking', description: '切换思考过程显示' },
  { name: '/sessions', description: '查看会话列表' },
  { name: '/stats', description: '查看使用统计' },
];

export function CommandPalette({ isOpen, onClose, onCommand }: CommandPaletteProps) {
  const [search, setSearch] = useState('');

  if (!isOpen) return null;

  const filteredCommands = COMMANDS.filter(
    (cmd) =>
      cmd.name.toLowerCase().includes(search.toLowerCase()) ||
      cmd.description.includes(search)
  );

  const handleCommand = (command: string) => {
    onCommand(command);
    setSearch('');
    onClose();
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-start justify-center pt-20 z-50"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-lg mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索命令..."
            className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 rounded-lg outline-none"
            autoFocus
          />
        </div>

        <div className="max-h-96 overflow-y-auto">
          {filteredCommands.length === 0 ? (
            <div className="p-4 text-center text-gray-500 dark:text-gray-400">
              没有找到命令
            </div>
          ) : (
            filteredCommands.map((cmd) => (
              <button
                key={cmd.name}
                onClick={() => handleCommand(cmd.name)}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors border-b border-gray-100 dark:border-gray-700 last:border-0"
              >
                <div className="font-mono text-primary font-semibold">{cmd.name}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {cmd.description}
                </div>
              </button>
            ))
          )}
        </div>

        <div className="p-3 bg-gray-50 dark:bg-gray-900 text-xs text-gray-500 dark:text-gray-400 rounded-b-lg">
          提示：在输入框中输入 / 开头的命令，或按 Ctrl+P 打开命令面板
        </div>
      </div>
    </div>
  );
}
