export type Sender = 'user' | 'assistant'

export interface FileAttachment {
  filename: string
  size: number
  contentType: string
  previewUrl?: string
}

export interface Message {
  id: string
  sender: Sender
  content: string
  createdAt: string
  attachments?: FileAttachment[]
}

export interface ChatState {
  messages: Message[]
  sessionId?: string
}
