import { Alert, Box, CircularProgress, Divider, Paper, Typography } from "@mui/material";
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ExamplePrompts from "../components/ExamplePrompts";
import Layout from "../components/Layout";
import ModelPicker from "../components/ModelPicker";
import ChatInput from "../components/chat/ChatInput";
import { useChat } from "../context/ChatContext";
import { useAssistantService } from "../hooks/useAssistantService";
import { AgentModel } from "../types/agentTypes";
import { ChatMessageData } from "../types/chatTypes";

const StartPage: React.FC = () => {
    const { selectedModel, setSelectedModel, setMessages } = useChat();
    const { loading, error, getAvailableModels } = useAssistantService();
    const [availableModels, setAvailableModels] = useState<AgentModel[]>([]);
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

    const handleModelChange = (model: AgentModel) => {
        setSelectedModel(model);
    };

    const handleSelectExample = (example: string) => {
        if (!selectedModel) {
            alert("Please select a model first");
            return;
        }

        const userMessage: ChatMessageData = {
            message: example,
            base64_image: null,
            isUser: true,
        };

        setMessages([userMessage]);
        navigate("/chat");
    };

    const handleSendMessage = (message: ChatMessageData) => {
        if (!message || !selectedModel) return;

        setMessages([message]);
        navigate("/chat");
    };

    return (
        <Layout>
            <Paper
                elevation={16}
                sx={{
                    padding: 2,
                    borderRadius: 2,
                    width: { xl: "60vw", md: "80vw", xs: "100vw" },
                }}
            >
                <Box sx={{ display: "flex", justifyContent: "center" }}>
                    <Typography variant="h5" gutterBottom>
                        🔮 Explore FUNDus!
                    </Typography>
                </Box>

                {loading && (
                    <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
                        <CircularProgress />
                    </Box>
                )}

                {error && (
                    <Box sx={{ p: 2, width: "100%" }}>
                        <Alert severity="error">Error Loading Models!</Alert>
                    </Box>
                )}

                {availableModels.length === 0 && !loading && !error && (
                    <Alert severity="warning">No models available!</Alert>
                )}

                {availableModels.length > 0 && (
                    <>
                        <ModelPicker
                            selectedModel={selectedModel}
                            models={availableModels}
                            onModelChange={handleModelChange}
                            isLoading={loading}
                            isError={!!error}
                        />

                        <Divider sx={{ marginY: 2 }} />

                        <ExamplePrompts onSelectExample={handleSelectExample} />

                        <Box sx={{ mt: "auto" }}>
                            <Divider sx={{ my: 1 }} />
                            <ChatInput
                                onSendMessage={handleSendMessage}
                                onReset={() => {}}
                                disabled={!selectedModel || loading || !!error}
                                showAddImage={true}
                            />
                        </Box>
                    </>
                )}
            </Paper>
        </Layout>
    );
};

export default StartPage;
