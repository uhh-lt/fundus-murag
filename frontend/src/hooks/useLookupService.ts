import { useCallback, useState } from 'react';
import lookupService from '../services/lookupService';
import { FundusCollection, FundusRecord, FundusRecordImage } from '../types/fundusTypes';


export function useAssistantService() {
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<Error | null>(null);

    const getFundusRecord = useCallback(async (murag_id: string): Promise<FundusRecord | undefined> => {
        setLoading(true);
        setError(null);
        try {
            const record = await lookupService.getFundusRecord(murag_id);
            return record;
        } catch (err) {
            setError(err as Error);
            return undefined;
        } finally {
            setLoading(false);
        }
    }, []);

    const getFundusRecordImage = useCallback(async (murag_id: string): Promise<FundusRecordImage | undefined> => {
        setLoading(true);
        setError(null);
        try {
            const record = await lookupService.getFundusRecordImage(murag_id);
            return record;
        } catch (err) {
            setError(err as Error);
            return undefined;
        } finally {
            setLoading(false);
        }
    }, []);

    const getFundusCollection = useCallback(async (murag_id: string): Promise<FundusCollection | undefined> => {
        setLoading(true);
        setError(null);
        try {
            const record = await lookupService.getFundusCollection(murag_id);
            return record;
        } catch (err) {
            setError(err as Error);
            return undefined;
        } finally {
            setLoading(false);
        }
    }, []);

    return { loading, error, getFundusRecord, getFundusRecordImage, getFundusCollection };
}
