import Brightness4Icon from "@mui/icons-material/Brightness4";
import Brightness7Icon from "@mui/icons-material/Brightness7";
import { AppBar, Box, IconButton, Toolbar, Typography } from "@mui/material";
import React from "react";
import { Link } from "react-router-dom";
import { useTheme } from "../context/ThemeContext";

interface LayoutProps {
    children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
    const { mode, toggleColorMode } = useTheme();

    return (
        <Box
            sx={{
                minHeight: "100vh",
                minWidth: "100vw",
                m: 0,
                p: 0,
                position: "fixed",
                overflow: "hidden",
            }}
        >
            <AppBar>
                <Toolbar>
                    <Typography variant="h6" sx={{ flexGrow: 1 }}>
                        <Link to="/" style={{ color: "inherit", textDecoration: "none" }}>
                            🔮 FUNDus Assistant
                        </Link>
                    </Typography>
                    <IconButton onClick={toggleColorMode} color="inherit">
                        {mode === "dark" ? <Brightness7Icon /> : <Brightness4Icon />}
                    </IconButton>
                </Toolbar>
            </AppBar>
            <Box
                sx={{
                    minWidth: "100vw",
                    maxWidth: "100vw",
                    minHeight: "calc(100vh - 64px)",
                    maxHeight: "calc(100vh - 64px)",
                    mt: "64px",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                }}
            >
                {children}
            </Box>
        </Box>
    );
};

export default Layout;
