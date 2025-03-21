import AddPhotoAlternateIcon from "@mui/icons-material/AddPhotoAlternate";
import RestoreIcon from "@mui/icons-material/Restore";
import SendIcon from "@mui/icons-material/Send";
import { Badge, Box, IconButton, TextField, Tooltip } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { KeyboardEvent, useState } from "react";
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

    const handleSend = () => {
        console.log("Sending message:", message);
        if (message && (message!.message.trim() || message.base64_image)) {
            onSendMessage(message);
            setMessage(null);
            setHasImage(false);
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
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
            base64_image: message?.base64_image || null,
            isUser: true,
        });
    };

    const onAddImage = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        const file = files[0];
        const reader = new FileReader();

        reader.onload = (event) => {
            if (event.target && typeof event.target.result === "string") {
                const base64String = event.target.result;

                console.log("Image uploaded:", base64String);

                // Currently we only support searching for similar images when the user uploads an image
                const imageMessage: ChatMessageData = {
                    message: "Find FundusRecords with similar images to this one",
                    base64_image: base64String,
                    isUser: true,
                };

                // Set the message and update UI
                setMessage(imageMessage);
                setHasImage(true);

                // Send message after a short delay to allow the UI to update
                // setTimeout(() => {
                //     onSendMessage(imageMessage);
                //     setMessage(null);
                //     setHasImage(false);
                // }, 100);
            }
        };

        reader.readAsDataURL(file);
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
            {showAddImage && (
                <Tooltip title="Add an image">
                    <IconButton color="info" disabled={disabled} component="label" size="large" sx={{ mr: 2 }}>
                        <Badge color="info" variant="dot" invisible={!hasImage}>
                            <AddPhotoAlternateIcon />
                        </Badge>
                        <VisuallyHiddenInput type="file" onChange={onAddImage} accept="image/*" />
                    </IconButton>
                </Tooltip>
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
                        onClick={handleSend}
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
