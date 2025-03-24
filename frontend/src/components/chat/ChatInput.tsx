import AddPhotoAlternateIcon from "@mui/icons-material/AddPhotoAlternate";
import RestoreIcon from "@mui/icons-material/Restore";
import SendIcon from "@mui/icons-material/Send";
import { Badge, Box, CircularProgress, IconButton, TextField, Tooltip } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { KeyboardEvent, useState } from "react";
import { useUserImageService } from "../../hooks/useUserImageService";
import { ChatMessageData } from "../../types/chatTypes";

interface ChatInputProps {
    onSendMessage: (message: ChatMessageData) => void;
    onReset: () => void;
    disabled?: boolean;
    showAddImage?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, onReset, showAddImage = false, disabled = false }) => {
    const [message, setMessage] = useState<ChatMessageData | null>(null);
    const [hasImage, setHasImage] = useState<boolean>(false);

    const { error, loading, storeUserImage } = useUserImageService();

    const sendMessage = () => {
        if (message && (message!.message.trim() || message.user_image_id)) {
            onSendMessage(message);
            setMessage(null);
            setHasImage(false);
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const handleTextFieldOnChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const msg = e.target.value;
        if (msg.length === 0 && !hasImage) {
            setMessage(null);
            return;
        }
        setMessage({
            message: msg,
            user_image_id: message?.user_image_id || null,
            isUser: true,
        });
    };

    const onAddImage = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        const file = files[0];

        storeUserImage(file).then((image_id) => {
            if (image_id) {
                const imageMessage: ChatMessageData = {
                    message: "Find FundusRecords with similar images to this one",
                    user_image_id: image_id,
                    isUser: true,
                };

                setMessage(imageMessage);
                setHasImage(true);

                // Automatically send the message when an image is uploaded
                onSendMessage(imageMessage);
            }
        });
    };

    const VisuallyHiddenInput = styled("input")({
        clip: "rect(0 0 0 0)",
        clipPath: "inset(50%)",
        height: 1,
        overflow: "hidden",
        position: "absolute",
        bottom: 0,
        left: 0,
        whiteSpace: "nowrap",
        width: 1,
    });

    return (
        <Box display="flex" alignItems="center">
            {showAddImage && !(loading || error) && (
                <Tooltip title="Add an image">
                    <IconButton color="info" disabled={disabled} component="label" size="large" sx={{ mr: 2 }}>
                        <Badge color="info" variant="dot" invisible={!hasImage}>
                            <AddPhotoAlternateIcon />
                        </Badge>
                        <VisuallyHiddenInput type="file" onChange={onAddImage} accept="image/*" />
                    </IconButton>
                </Tooltip>
            )}
            {showAddImage && loading && (
                <Box sx={{ mr: 2 }}>
                    <Tooltip title="Uploading image">
                        <CircularProgress size={24} />
                    </Tooltip>
                </Box>
            )}
            {showAddImage && error && (
                <Box sx={{ mr: 2 }}>
                    <Tooltip title="Error uploading image">
                        <IconButton color="error" disabled>
                            <AddPhotoAlternateIcon />
                        </IconButton>
                    </Tooltip>
                </Box>
            )}
            <TextField
                fullWidth
                placeholder="Enter a question ..."
                value={message?.message || ""}
                onChange={handleTextFieldOnChange}
                onKeyDown={handleKeyDown}
                disabled={disabled}
                multiline
                maxRows={4}
            />
            <Box ml={2} display="flex">
                <Tooltip title="Send your message">
                    <IconButton
                        color="primary"
                        onClick={sendMessage}
                        disabled={disabled || ((!message?.message || message.message.trim() === "") && !hasImage)}
                    >
                        <SendIcon />
                    </IconButton>
                </Tooltip>
                <Tooltip title="Start a new conversation">
                    <IconButton color="secondary" onClick={onReset} disabled={disabled}>
                        <RestoreIcon />
                    </IconButton>
                </Tooltip>
            </Box>
        </Box>
    );
};

export default ChatInput;
