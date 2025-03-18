import React, { createContext, ReactNode, useContext, useState } from "react";

import { AssistantModel } from "../types/assistantTypes";
import { ChatMessageData } from "../types/chatTypes";

interface ChatContextType {
    messages: ChatMessageData[];
    setMessages: React.Dispatch<React.SetStateAction<ChatMessageData[]>>;
    selectedModel: AssistantModel | undefined;
    setSelectedModel: React.Dispatch<React.SetStateAction<AssistantModel | undefined>>;
    sessionId: string | undefined | null;
    setSessionId: React.Dispatch<React.SetStateAction<string | undefined | null>>;
}

interface ChatProviderProps {
    children: ReactNode;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = (): ChatContextType => {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error("useChat must be used within a ChatProvider");
    }
    return context;
};
export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
    const [messages, setMessages] = useState<ChatMessageData[]>([]);
    const [sessionId, setSessionId] = useState<string | undefined | null>(undefined);
    const [selectedModel, setSelectedModel] = useState<AssistantModel | undefined>();

    return (
        <ChatContext.Provider
            value={{
                messages,
                setMessages,
                selectedModel,
                setSelectedModel,
                sessionId,
                setSessionId,
            }}
        >
            {children}
        </ChatContext.Provider>
    );
};

export default ChatContext;
