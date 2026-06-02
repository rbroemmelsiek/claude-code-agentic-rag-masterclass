import { useState, useRef } from 'react'
import { ThreadList, ThreadListRef } from '@/components/chat/ThreadList'
import { ChatView } from '@/components/chat/ChatView'
import { UserMenu } from '@/components/UserMenu'
import { useAuth } from '@/hooks/useAuth'

export function ChatPage() {
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const { signOut, user } = useAuth()
  const threadListRef = useRef<ThreadListRef>(null)

  const handleThreadTitleUpdate = (threadId: string, title: string) => {
    threadListRef.current?.updateThreadTitle(threadId, title)
  }

  const handleSignOut = async () => {
    try {
      await signOut()
    } catch (error) {
      console.error('Failed to sign out:', error)
    }
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="flex w-64 flex-col border-r bg-muted/30">
        <div className="border-b p-4">
          <h1 className="text-lg font-semibold">RAG Chat</h1>
        </div>
        <ThreadList
          ref={threadListRef}
          selectedThreadId={selectedThreadId}
          onSelectThread={setSelectedThreadId}
        />
        <div className="border-t p-2">
          {user?.email && (
            <UserMenu email={user.email} onSignOut={handleSignOut} />
          )}
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1">
        {selectedThreadId ? (
          <ChatView
            threadId={selectedThreadId}
            onThreadTitleUpdate={handleThreadTitleUpdate}
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="text-center text-muted-foreground">
              <p className="text-lg">Welcome to RAG Chat</p>
              <p className="text-sm">Select a conversation or start a new one</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
