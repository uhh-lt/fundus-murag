export interface AgentModel {
    name: string;
    display_name: string;
  }

  export interface AgentSession {
    session_id: string;
    created: number;
    updated: number;
    expires: number;
  }

  export interface AgentResponse {
    message: string;
    session: AgentSession;
  }

  export interface UserMessageRequest {
    message: string;
    base64_images: string[] | undefined | null;
    model_name: string;
    session_id: string | undefined | null;
  }
