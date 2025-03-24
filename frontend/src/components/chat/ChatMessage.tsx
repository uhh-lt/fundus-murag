import { Box, CircularProgress, Divider, Paper, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useUserImageService } from "../../hooks/useUserImageService";
import { ChatMessageData } from "../../types/chatTypes";
import FundusCollectionCard from "./FundusCollectionCard";
import FundusRecordCard from "./FundusRecordCard";

const FUNDUS_RECORD_RENDER_TAG_OPEN = "<FundusRecord";
const FUNDUS_COLLECTION_RENDER_TAG_OPEN = "<FundusCollection";
const RENDER_TAG_MURAG_ID_ATTRIBUTE = "murag_id";
const RENDER_TAG_CLOSE = "/>";

// Helper function to get the regex pattern for a specific tag
const getRenderTagPattern = (renderTagOpen: string, global: boolean = false): RegExp => {
    return new RegExp(
        renderTagOpen +
            "\\s+" +
            RENDER_TAG_MURAG_ID_ATTRIBUTE +
            "\\s*=\\s*(['\"])" +
            "([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89aAbB][0-9a-fA-F]{3}-[0-9a-fA-F]{12})" +
            "\\1\\s*" +
            RENDER_TAG_CLOSE,
        global ? "g" : "",
    );
};

// Helper functions for FundusRecord tags
const containsFundusRecordTag = (content: string): boolean => {
    const pattern = getRenderTagPattern(FUNDUS_RECORD_RENDER_TAG_OPEN);
    return pattern.test(content);
};

const extractFundusRecordIds = (content: string): string[] => {
    const pattern = getRenderTagPattern(FUNDUS_RECORD_RENDER_TAG_OPEN, true);
    const matches = Array.from(content.matchAll(pattern));
    return matches.map((match) => match[2]);
};

const replaceFundusRecordTags = (content: string): string => {
    const pattern = getRenderTagPattern(FUNDUS_RECORD_RENDER_TAG_OPEN, true);
    return content.replace(pattern, "");
};

// Helper functions for FundusCollection tags
const containsFundusCollectionTag = (content: string): boolean => {
    const pattern = getRenderTagPattern(FUNDUS_COLLECTION_RENDER_TAG_OPEN);
    return pattern.test(content);
};

const extractFundusCollectionIds = (content: string): string[] => {
    const pattern = getRenderTagPattern(FUNDUS_COLLECTION_RENDER_TAG_OPEN, true);
    const matches = Array.from(content.matchAll(pattern));
    return matches.map((match) => match[2]);
};

const replaceFundusCollectionTags = (content: string): string => {
    const pattern = getRenderTagPattern(FUNDUS_COLLECTION_RENDER_TAG_OPEN, true);
    return content.replace(pattern, "");
};

const cleanUpWhitespaces = (content: string): string => {
    // replace all multiple spaces (not newlines!) with a single space
    content = content.replace(/ +/g, " ");
    // replace more than 2 newlines with 2 newlines
    content = content.replace(/\n{3,}/g, "\n\n");
    // replace empty list items
    content = content.replace(/^[-*+•] \n/gm, "");
    return content;
};

interface ChatMessageProps {
    chatMessage: ChatMessageData;
    senderName: string;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ chatMessage, senderName }) => {
    const { error, loading, getUserImage } = useUserImageService();
    const [userImage, setUserImage] = useState<string | undefined>(undefined);

    useEffect(() => {
        if (chatMessage.isUser && chatMessage.user_image_id) {
            getUserImage(chatMessage.user_image_id).then((image) => {
                setUserImage(image);
            });
        }
    }, [chatMessage.isUser, chatMessage.user_image_id, getUserImage]);

    // Only process custom tags for non-user messages
    if (!chatMessage.isUser) {
        const hasRecordTags = containsFundusRecordTag(chatMessage.message);
        const hasCollectionTags = containsFundusCollectionTag(chatMessage.message);

        // Extract IDs for both types of tags
        const recordIds = hasRecordTags ? extractFundusRecordIds(chatMessage.message) : [];
        const collectionIds = hasCollectionTags ? extractFundusCollectionIds(chatMessage.message) : [];

        // Clean content
        let cleanContent = chatMessage.message;
        if (hasRecordTags) {
            cleanContent = replaceFundusRecordTags(cleanContent);
        }
        if (hasCollectionTags) {
            cleanContent = replaceFundusCollectionTags(cleanContent);
        }
        cleanContent = cleanUpWhitespaces(cleanContent);

        return (
            <Box sx={{ display: "flex", justifyContent: "flex-start" }}>
                <Paper elevation={4} sx={{ px: 2, py: 1, my: 1, mx: 2, bgcolor: "primary.main", width: "90%" }}>
                    <Typography variant="subtitle2">{senderName}</Typography>
                    <Divider />
                    <Box mt={1}>
                        {/* Regular text content */}
                        {cleanContent && (
                            <Typography component="div" sx={{ whiteSpace: "pre-wrap" }}>
                                <Markdown remarkPlugins={[remarkGfm]}>{cleanContent}</Markdown>
                            </Typography>
                        )}

                        {/* Render FundusRecord components in a Grid layout */}
                        {recordIds.length > 0 && (
                            <Grid container spacing={2} sx={{ flexGrow: 1 }}>
                                {recordIds.map((id, index) => (
                                    <Grid size={{ xs: 12, md: 4 }} key={`record-${id}-${index}`}>
                                        <FundusRecordCard muragId={id} />
                                    </Grid>
                                ))}
                            </Grid>
                        )}

                        {/* Render FundusCollection components */}
                        {collectionIds.map((id, index) => (
                            <FundusCollectionCard key={`collection-${id}-${index}`} muragId={id} />
                        ))}
                    </Box>
                </Paper>
            </Box>
        );
    }

    // For user messages, render normally
    return (
        <Box sx={{ display: "flex", justifyContent: "flex-end", textAlign: "right" }}>
            <Paper
                elevation={4}
                sx={{
                    px: 2,
                    py: 1,
                    my: 1,
                    mx: 2,
                    bgcolor: "secondary.dark",
                    maxWidth: "90%",
                    minWidth: "33%",
                }}
            >
                <Typography variant="subtitle2">{senderName}</Typography>
                <Divider />
                <Box mt={1}>
                    <Typography component="div" sx={{ whiteSpace: "pre-wrap" }}>
                        <Markdown remarkPlugins={[remarkGfm]}>{chatMessage.message}</Markdown>
                    </Typography>
                    {userImage && (
                        <img
                            src={userImage}
                            alt="User image"
                            style={{
                                width: "200px",
                                height: "auto",
                                borderRadius: 8,
                            }}
                        />
                    )}
                    {chatMessage.user_image_id && loading && <CircularProgress />}
                    {chatMessage.user_image_id && error && (
                        <Typography color="error">Error loading user image</Typography>
                    )}
                </Box>
            </Paper>
        </Box>
    );
};

export default ChatMessage;
