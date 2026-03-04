# Doraemon Frontend (Next.js)

Modern web interface for Doraemon AI assistant built with Next.js, TypeScript, and Tailwind CSS.

## Features

- 🎨 Modern UI with Tailwind CSS
- ⚡ Real-time streaming responses via WebSocket
- 🔐 JWT authentication
- 📱 Responsive design
- 🎯 Type-safe with TypeScript
- 🔄 Auto-reconnect on connection loss

## Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS 4** - Utility-first CSS
- **Zustand** - State management
- **WebSocket** - Real-time communication

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend server running on port 8765

### Installation

```bash
cd frontend-next
npm install
```

### Development

```bash
npm run dev
```

Open http://localhost:3000 in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8765
NEXT_PUBLIC_WS_URL=ws://localhost:8765/ws
```

## Default Credentials

- Username: `admin`
- Password: `admin123`

## Project Structure

```
frontend-next/
├── app/                    # Next.js App Router
│   ├── login/             # Login page
│   └── chat/              # Chat interface
├── components/            # React components
│   ├── auth/             # Authentication
│   ├── chat/             # Chat UI
│   └── layout/           # Layout components
├── lib/                   # Utilities
│   ├── api.ts            # API client
│   └── websocket.ts      # WebSocket manager
├── hooks/                 # Custom React hooks
├── store/                 # Zustand stores
└── types/                 # TypeScript types
```

## WebSocket Protocol

### Client → Server

```typescript
// Authenticate
{ type: 'auth', token: string }

// Send message
{ type: 'message', content: string }

// Heartbeat
{ type: 'ping' }
```

### Server → Client

```typescript
// Auth success
{ type: 'auth_success', user_id: string }

// Status update
{ type: 'status', status: 'thinking' | 'streaming' }

// Streaming content
{ type: 'chunk', content: string }

// Complete
{ type: 'complete', content: string }

// Error
{ type: 'error', message: string }
```

## Future Enhancements

- [ ] Markdown rendering
- [ ] Code syntax highlighting
- [ ] Session management
- [ ] Dark mode
- [ ] File upload
- [ ] Message search
