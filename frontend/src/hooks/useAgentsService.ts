import { useCallback, useState } from 'react';
import agentsApiService from '../services/agentsApiService';
import { AgentModel, AgentResponse, AgentSession, UserMessageRequest } from '../types/agentTypes';

export function useAgentsService() {
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<Error | null>(null);

    const getAvailableModels = useCallback(async (): Promise<AgentModel[]> => {
        setLoading(true);
        setError(null);
        try {
            const models = await agentsApiService.getAvailableModels();
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
            const response = await agentsApiService.sendMessage(msg);
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
            const sessions = await agentsApiService.listSessions();
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
