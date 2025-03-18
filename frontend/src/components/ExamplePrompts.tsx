import { Box, Paper, Tooltip, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";
import React from "react";
const EXAMPLE_PROMPTS = [
    "What is FUNDus?",
    "What functionality do you provide?",
    "What collections are contained in FUNDus?",
    "Help me creating an biology exam for my students on the topic of beatles. Assist me.",
    "Show me a random FUNDus! record!",
    "Show me an image depicting a greek statue!",
    "I to prepare a presentation on minerals for by geology class. Can you help me?",
    "I want to learn about ancient history. Tell me about it.",
];
interface ExamplePromptsProps {
    onSelectExample: (example: string) => void;
}

const ExamplePrompts: React.FC<ExamplePromptsProps> = ({ onSelectExample }) => {
    return (
        <Box my={2} p={2}>
            <Typography variant="h6" gutterBottom>
                Try one of these examples or type your own question:
            </Typography>

            <Grid container spacing={2} justifyContent="start" flexWrap="wrap">
                {EXAMPLE_PROMPTS.map((example, index) => (
                    <Grid size={3} key={index}>
                        <Tooltip title="Click to use this example">
                            <Paper
                                elevation={3}
                                onClick={() => onSelectExample(example)}
                                sx={{
                                    cursor: "pointer",
                                    height: "100%",
                                    borderRadius: 2,
                                    bgcolor: "primary.main",
                                    color: "primary.contrastText",
                                    p: 2,
                                }}
                            >
                                <Typography variant="body1">{example}</Typography>
                            </Paper>
                        </Tooltip>
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
};

export default ExamplePrompts;
