import RestoreIcon from "@mui/icons-material/Restore";
import SendIcon from "@mui/icons-material/Send";
import { Box, IconButton, TextField, Tooltip } from "@mui/material";
import React, { KeyboardEvent, useState } from "react";

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    onReset: () => void;
    disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, onReset, disabled = false }) => {
    const [message, setMessage] = useState("");

    const handleSend = () => {
        if (message.trim()) {
            onSendMessage(message);
            setMessage("");
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <Box display="flex" alignItems="center">
            <TextField
                fullWidth
                placeholder="Enter a question ..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={disabled}
                multiline
                maxRows={4}
            />
            <Box ml={2} display="flex">
                <Tooltip title="Send your message">
                    <span>
                        <IconButton color="primary" onClick={handleSend} disabled={disabled}>
                            <SendIcon />
                        </IconButton>
                    </span>
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
