export type WSMessageType =
  | 'auth'
  | 'message'
  | 'ping'
  | 'auth_success'
  | 'status'
  | 'chunk'
  | 'complete'
  | 'error'
  | 'pong';

export interface WSMessage {
  type: WSMessageType;
  [key: string]: any;
}

export interface WSAuthMessage extends WSMessage {
  type: 'auth';
  token: string;
}

export interface WSUserMessage extends WSMessage {
  type: 'message';
  content: string;
}

export interface WSChunkMessage extends WSMessage {
  type: 'chunk';
  content: string;
}

export interface WSStatusMessage extends WSMessage {
  type: 'status';
  status: string;
}

export interface WSCompleteMessage extends WSMessage {
  type: 'complete';
  content: string;
}

export interface WSErrorMessage extends WSMessage {
  type: 'error';
  message: string;
}
