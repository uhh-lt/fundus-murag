export interface AssistantModel {
    name: string;
    display_name: string;
  }

  export interface AssistantSession {
    session_id: string;
    model_name: string;
    created: number;
  }

  export interface AssistantResponse {
    message: string;
    session: AssistantSession;
  }

  export interface UserMessageRequest {
    message: string;
    base64_images: string[] | undefined | null;
    model_name: string;
    session_id: string | undefined | null;
  }
