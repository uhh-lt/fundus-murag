import CssBaseline from '@mui/material/CssBaseline';
import React from 'react';
import ReactDOM from 'react-dom/client';
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router";
import ChatPage from './pages/ChatPage';
import StartPage from './pages/StartPage';

import { ChatProvider } from './context/ChatContext';
import { ThemeProvider } from './context/ThemeContext';

const router = createBrowserRouter([
  {
    path: "/",
    Component: StartPage,
  },
  {
    path: "/chat",
    Component: ChatPage,
  }
]);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <CssBaseline />

    <ThemeProvider>
      <CssBaseline />
      <ChatProvider>
        <RouterProvider router={router} />
      </ChatProvider>
    </ThemeProvider>
  </React.StrictMode>
)
