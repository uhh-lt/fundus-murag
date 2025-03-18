import { Alert, Box, CircularProgress, Container, Divider, Paper, Typography } from "@mui/material";
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ExamplePrompts from "../components/ExamplePrompts";
import Layout from "../components/Layout";
import ModelPicker from "../components/ModelPicker";
import ChatInput from "../components/chat/ChatInput";
import { useChat } from "../context/ChatContext";
import { useAssistantService } from "../hooks/useAssistantService";
import { AssistantModel } from "../types/assistantTypes";
import { ChatMessageData } from "../types/chatTypes";

const StartPage: React.FC = () => {
    const { selectedModel, setSelectedModel, setMessages } = useChat();
    const {
        loading: assistantServiceLoading,
        error: assistantServiceError,
        getAvailableModels,
    } = useAssistantService();
    const [availableModels, setAvailableModels] = useState<AssistantModel[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchModels = async () => {
            const models = await getAvailableModels();
            setAvailableModels(models);
            const defaultModel = models.find((model) => model.name === "google/gemini-2.0-flash");
            setSelectedModel(defaultModel);
        };

        fetchModels();
    }, [getAvailableModels, setSelectedModel]);

    const handleModelChange = (model: AssistantModel) => {
        setSelectedModel(model);
    };

    const handleSelectExample = (example: string) => {
        if (!selectedModel) {
            alert("Please select a model first");
            return;
        }

        const userMessage: ChatMessageData = {
            message: example,
            base64_images: null,
            isUser: true,
        };

        setMessages([userMessage]);
        navigate("/chat");
    };

    const handleSendMessage = (content: string) => {
        if (!content.trim() || !selectedModel) return;

        const userMessage = {
            message: content,
            base64_images: null,
            isUser: true,
            sessionId: undefined,
        };

        setMessages([userMessage]);
        navigate("/chat");
    };

    return (
        <Layout>
            <Container sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
                <Paper
                    elevation={16}
                    sx={{
                        display: "flex",
                        flexDirection: "column",
                        padding: 2,
                        borderRadius: 2,
                        minHeight: "50vh",
                        maxHeight: "80vh",
                        width: "100%",
                    }}
                >
                    <Box sx={{ display: "flex", justifyContent: "center" }}>
                        <Typography variant="h5" gutterBottom>
                            🔮 Explore FUNDus!
                        </Typography>
                    </Box>

                    {assistantServiceLoading && (
                        <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
                            <CircularProgress />
                        </Box>
                    )}

                    {assistantServiceError && (
                        <Box sx={{ p: 2, width: "100%" }}>
                            <Alert severity="error">Error Loading Models!</Alert>
                        </Box>
                    )}

                    {availableModels.length === 0 && !assistantServiceLoading && !assistantServiceError && (
                        <Alert severity="warning">No models available!</Alert>
                    )}

                    {availableModels.length > 0 && (
                        <>
                            <ModelPicker
                                selectedModel={selectedModel}
                                models={availableModels}
                                onModelChange={handleModelChange}
                                isLoading={assistantServiceLoading}
                                isError={!!assistantServiceError}
                            />

                            <Divider sx={{ marginY: 2 }} />

                            <ExamplePrompts onSelectExample={handleSelectExample} />

                            <Box sx={{ mt: "auto" }}>
                                <ChatInput
                                    onSendMessage={handleSendMessage}
                                    onReset={() => {}}
                                    disabled={!selectedModel || assistantServiceLoading || !!assistantServiceError}
                                />
                            </Box>
                        </>
                    )}
                </Paper>
            </Container>
        </Layout>
    );
};

export default StartPage;
