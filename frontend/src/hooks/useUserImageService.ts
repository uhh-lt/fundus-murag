import { useCallback, useState } from 'react';
import userImageApiService from '../services/userImageApiService';


export function useUserImageService() {
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<Error | null>(null);

    const storeUserImage = useCallback(async (file: File): Promise<string | undefined> => {
        setLoading(true);
        setError(null);
        try {
            const imagePath = await userImageApiService.storeUserImage(file);
            return imagePath;
        } catch (err) {
            setError(err as Error);
            return undefined;
        } finally {
            setLoading(false);
        }
    }, []);

    const getUserImage = useCallback(async (userImageId: string): Promise<string | undefined> => {
        setLoading(true);
        setError(null);
        try {
            const base64Image = await userImageApiService.getUserImage(userImageId);
            return base64Image;
        } catch (err) {
            setError(err as Error);
            return undefined;
        } finally {
            setLoading(false);
        }
    }, []);

    return { loading, error, storeUserImage, getUserImage };
}
