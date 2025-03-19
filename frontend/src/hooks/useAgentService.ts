import { useCallback, useState } from 'react';
import agentService from '../services/agentService';
import { AgentModel, AgentResponse, AgentSession, UserMessageRequest } from '../types/agentTypes';

export function useAgentService() {
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<Error | null>(null);

    const getAvailableModels = useCallback(async (): Promise<AgentModel[]> => {
        setLoading(true);
        setError(null);
        try {
            const models = await agentService.getAvailableModels();
            return models;
        } catch (err) {
            setError(err as Error);
            return [];
        } finally {
            setLoading(false);
        }
    }, []);

    const sendMessage = useCallback(async (msg: UserMessageRequest): Promise<AgentResponse | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await agentService.sendMessage(msg);
            return response;
        } catch (err) {
            setError(err as Error);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const listSessions = useCallback(async (): Promise<AgentSession[] | null> => {
        setLoading(true);
        setError(null);
        try {
            const sessions = await agentService.listSessions();
            return sessions;
        } catch (err) {
            setError(err as Error);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    return { loading, error, getAvailableModels, sendMessage, listSessions };
}
