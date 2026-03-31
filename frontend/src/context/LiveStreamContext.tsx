import { createContext, useContext, type ReactNode } from 'react';
import { useLiveStream } from '../hooks/useLiveStream';

type LiveStreamContextValue = ReturnType<typeof useLiveStream>;

const LiveStreamContext = createContext<LiveStreamContextValue | null>(null);

type LiveStreamProviderProps = {
  children: ReactNode;
};

export function LiveStreamProvider({ children }: LiveStreamProviderProps) {
  const liveStream = useLiveStream();

  return <LiveStreamContext.Provider value={liveStream}>{children}</LiveStreamContext.Provider>;
}

export function useLiveStreamContext(): LiveStreamContextValue {
  const context = useContext(LiveStreamContext);

  if (!context) {
    throw new Error('useLiveStreamContext must be used within LiveStreamProvider');
  }

  return context;
}
