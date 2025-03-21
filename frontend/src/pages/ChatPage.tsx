import { Alert, Box, Divider, Paper, Typography } from "@mui/material";
import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import ChatInput from "../components/chat/ChatInput";
import ChatMessage from "../components/chat/ChatMessage";
import { useChat } from "../context/ChatContext";
import { useAssistantService } from "../hooks/useAssistantService";
import { UserMessageRequest } from "../types/agentTypes";
import { ChatMessageData } from "../types/chatTypes";

const ChatPage: React.FC = () => {
    const { messages, setMessages, sessionId, setSessionId, selectedModel } = useChat();
    const { loading, error, sendMessage } = useAssistantService();

    const navigate = useNavigate();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!selectedModel || messages.length === 0) {
            navigate("/");
        }
    }, [selectedModel, messages, navigate]);

    useEffect(() => {
        // Auto-scroll to bottom when messages change
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        // Process the first message from the user
        if (messages.length !== 1 || !selectedModel) {
            return;
        }

        const msg: UserMessageRequest = {
            message: messages[0].message,
            base64_image: messages[0].base64_image,
            model_name: selectedModel.name,
            session_id: null, // start a new session
        };
        sendMessage(msg).then((response) => {
            if (!response) {
                return;
            }
            setSessionId(response.session.session_id);
            const agentMessage: ChatMessageData = {
                message: response.message,
                isUser: false,
                base64_image: null,
            };
            setMessages((prev) => [...prev, agentMessage]);
        });
    }, []);

    const handleSendMessage = (message: ChatMessageData) => {
        if (!message || !selectedModel) return;

        setMessages((prev) => [...prev, message]);

        const msg: UserMessageRequest = {
            message: message.message,
            base64_image: message.base64_image,
            model_name: selectedModel.name,
            session_id: sessionId,
        };
        sendMessage(msg).then((response) => {
            if (!response) {
                return;
            }
            const agentMessage: ChatMessageData = {
                message: response.message,
                isUser: false,
                base64_image: null,
            };
            setMessages((prev) => [...prev, agentMessage]);
        });
    };

    const handleReset = () => {
        setMessages([]);
        navigate("/");
    };

    if (!selectedModel) {
        return null;
    }

    return (
        <Layout>
            <Box
                sx={{
                    width: { xl: "60vw", md: "80vw", xs: "100vw" },
                    height: "85vh",
                }}
            >
                {error && <Alert severity="error">Error Communicating with Agent!</Alert>}
                {!error && (
                    <Paper
                        elevation={16}
                        sx={{
                            p: 2,
                            borderRadius: 2,
                            height: "100%",
                            display: "flex",
                            flexDirection: "column",
                        }}
                    >
                        <Typography variant="h6">
                            🔮 Chat with <strong>FUNDus! Agent</strong> using <em>{selectedModel.display_name}</em>
                        </Typography>

                        <Divider sx={{ my: 1 }} />

                        <Box
                            sx={{
                                overflow: "scroll",
                                height: "100%",
                                px: { xs: 1, sm: 2 },
                            }}
                        >
                            {messages.map((msg, i) => (
                                <ChatMessage
                                    key={`msg-${i}`}
                                    chatMessage={msg}
                                    senderName={msg.isUser ? "You" : selectedModel.display_name}
                                />
                            ))}
                            {loading && (
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 1, fontStyle: "italic" }}>
                                    {selectedModel.display_name} is typing...
                                </Typography>
                            )}
                            <div ref={messagesEndRef} />
                        </Box>

                        <Divider sx={{ my: 1 }} />

                        <ChatInput onSendMessage={handleSendMessage} onReset={handleReset} disabled={loading} />
                    </Paper>
                )}
            </Box>
        </Layout>
    );
};

export default ChatPage;
