import { Alert, Box, Container, Divider, Paper, Typography } from "@mui/material";
import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import ChatInput from "../components/chat/ChatInput";
import ChatMessage from "../components/chat/ChatMessage";
import { useChat } from "../context/ChatContext";
import { useAssistantService } from "../hooks/useAssistantService";
import { UserMessageRequest } from "../types/assistantTypes";
import { ChatMessageData } from "../types/chatTypes";

const ChatPage: React.FC = () => {
    const { messages, setMessages, sessionId, setSessionId, selectedModel } = useChat();
    const { loading: assistantServiceLoading, error: assistantServiceError, sendMessage } = useAssistantService();

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
            base64_images: messages[0].base64_images,
            model_name: selectedModel.name,
            session_id: null, // start a new session
        };
        sendMessage(msg).then((response) => {
            if (!response) {
                return;
            }
            setSessionId(response.session.session_id);
            const assistantMessage: ChatMessageData = {
                message: response.message,
                isUser: false,
                base64_images: null,
            };
            setMessages((prev) => [...prev, assistantMessage]);
        });
    }, []);

    const handleSendMessage = (content: string) => {
        if (!content.trim() || !selectedModel) return;
        const userMessage: ChatMessageData = {
            message: content,
            base64_images: null,
            isUser: true,
        };
        setMessages((prev) => [...prev, userMessage]);

        const msg: UserMessageRequest = {
            message: content,
            base64_images: null,
            model_name: selectedModel.name,
            session_id: sessionId,
        };
        sendMessage(msg).then((response) => {
            if (!response) {
                return;
            }
            const assistantMessage: ChatMessageData = {
                message: response.message,
                isUser: false,
                base64_images: null,
            };
            setMessages((prev) => [...prev, assistantMessage]);
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
            <Container
                sx={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    minHeight: "100vh",
                    maxHeight: "100vh",
                    maxWidth: "100%",
                    minWidth: "60%",
                }}
            >
                {assistantServiceError && <Alert severity="error">Error Communicating with Assistant!</Alert>}
                {!assistantServiceError && (
                    <Paper elevation={3} sx={{ padding: 3, borderRadius: 2, width: "100%" }}>
                        <Typography variant="h6">
                            🔮 Chat with <strong>FUNDus! Assistant</strong> using <em>{selectedModel.display_name}</em>
                        </Typography>

                        <Divider sx={{ my: 2 }} />

                        <Box sx={{ minHeight: "70vh", maxHeight: "70vh", overflow: "auto" }}>
                            {messages.map((msg, i) => (
                                <ChatMessage
                                    key={`msg-${i}`}
                                    content={msg.message}
                                    isUser={msg.isUser}
                                    senderName={msg.isUser ? "You" : selectedModel.display_name}
                                />
                            ))}
                            {assistantServiceLoading && (
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 1, fontStyle: "italic" }}>
                                    {selectedModel.display_name} is typing...
                                </Typography>
                            )}
                            <div ref={messagesEndRef} />
                        </Box>

                        <ChatInput
                            onSendMessage={handleSendMessage}
                            onReset={handleReset}
                            disabled={assistantServiceLoading}
                        />
                    </Paper>
                )}
            </Container>
        </Layout>
    );
};

export default ChatPage;
