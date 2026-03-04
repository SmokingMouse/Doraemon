'use client';

import { useEffect } from 'react';

export type KeyboardShortcut = {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  action: () => void;
  description: string;
};

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[]) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const ctrlMatch = shortcut.ctrl === undefined || shortcut.ctrl === (e.ctrlKey || e.metaKey);
        const shiftMatch = shortcut.shift === undefined || shortcut.shift === e.shiftKey;
        const altMatch = shortcut.alt === undefined || shortcut.alt === e.altKey;
        const keyMatch = shortcut.key.toLowerCase() === e.key.toLowerCase();

        if (ctrlMatch && shiftMatch && altMatch && keyMatch) {
          e.preventDefault();
          shortcut.action();
          break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}

export const SHORTCUTS: KeyboardShortcut[] = [
  {
    key: 'k',
    ctrl: true,
    action: () => {},
    description: 'New chat',
  },
  {
    key: '/',
    ctrl: true,
    action: () => {},
    description: 'Focus input',
  },
  {
    key: 'p',
    ctrl: true,
    action: () => {},
    description: 'Command palette',
  },
  {
    key: 'd',
    ctrl: true,
    action: () => {},
    description: 'Toggle dark mode',
  },
  {
    key: '?',
    shift: true,
    action: () => {},
    description: 'Show shortcuts',
  },
];
