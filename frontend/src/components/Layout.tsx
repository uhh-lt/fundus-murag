import Brightness4Icon from "@mui/icons-material/Brightness4";
import Brightness7Icon from "@mui/icons-material/Brightness7";
import { AppBar, Container, IconButton, Toolbar, Typography } from "@mui/material";
import React from "react";
import { Link } from "react-router-dom";
import { useTheme } from "../context/ThemeContext";

interface LayoutProps {
    children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
    const { mode, toggleColorMode } = useTheme();

    return (
        <Container
            sx={{
                bgcolor: "background.default",
                color: "text.primary",
                minHeight: "100vh",
                minWidth: "100vw",
            }}
        >
            <AppBar position="fixed">
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
            {children}
        </Container>
    );
};

export default Layout;
