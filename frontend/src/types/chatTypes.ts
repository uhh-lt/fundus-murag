export interface ChatMessageData {
    message: string;
    base64_images: string[] | undefined | null;
    isUser: boolean;
}
