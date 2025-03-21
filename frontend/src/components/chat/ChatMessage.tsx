import { Box, Divider, Paper, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
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

interface ChatMessageProps {
    content: string;
    isUser: boolean;
    senderName: string;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ content, isUser, senderName }) => {
    // Only process custom tags for non-user messages
    if (!isUser) {
        const hasRecordTags = containsFundusRecordTag(content);
        const hasCollectionTags = containsFundusCollectionTag(content);

        // Extract IDs for both types of tags
        const recordIds = hasRecordTags ? extractFundusRecordIds(content) : [];
        const collectionIds = hasCollectionTags ? extractFundusCollectionIds(content) : [];

        // Clean content by removing both types of tags
        let cleanContent = content;
        if (hasRecordTags) {
            cleanContent = replaceFundusRecordTags(cleanContent);
        }
        if (hasCollectionTags) {
            cleanContent = replaceFundusCollectionTags(cleanContent);
        }

        return (
            <Box sx={{ display: "flex", justifyContent: "flex-start" }}>
                <Paper
                    elevation={4}
                    sx={{ px: 2, py: 1, my: 1, mx: 2, bgcolor: "primary.main", maxWidth: "80%", minWidth: "40%" }}
                >
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
                            <Grid container spacing={2} columns={12}>
                                {recordIds.map((id, index) => (
                                    <Grid size={{ xs: 12, sm: 6, lg: 4 }} key={`record-${id}-${index}`}>
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
        <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
            <Paper
                elevation={4}
                sx={{ px: 2, py: 1, my: 1, mx: 2, bgcolor: "secondary.dark", maxWidth: "80%", minWidth: "40%" }}
            >
                <Typography variant="subtitle2" align="right">
                    {senderName}
                </Typography>
                <Divider />
                <Box mt={1}>
                    <Typography component="div" sx={{ whiteSpace: "pre-wrap" }}>
                        <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
                    </Typography>
                </Box>
            </Paper>
        </Box>
    );
};

export default ChatMessage;
