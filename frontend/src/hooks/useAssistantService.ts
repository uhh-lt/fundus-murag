import { useCallback, useState } from 'react';
import assistantService from '../services/assistantService';
import { AssistantModel, AssistantResponse, AssistantSession, UserMessageRequest } from '../types/assistantTypes';

export function useAssistantService() {
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<Error | null>(null);

    const getAvailableModels = useCallback(async (): Promise<AssistantModel[]> => {
        setLoading(true);
        setError(null);
        try {
            const models = await assistantService.getAvailableModels();
            return models;
        } catch (err) {
            setError(err as Error);
            return [];
        } finally {
            setLoading(false);
        }
    }, []);

    const sendMessage = useCallback(async (msg: UserMessageRequest): Promise<AssistantResponse | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await assistantService.sendMessage(msg);
            return response;
        } catch (err) {
            setError(err as Error);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const listSessions = useCallback(async (): Promise<AssistantSession[] | null> => {
        setLoading(true);
        setError(null);
        try {
            const sessions = await assistantService.listSessions();
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
