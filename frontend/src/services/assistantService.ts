import { AssistantModel, AssistantResponse, AssistantSession, UserMessageRequest } from "../types/assistantTypes";

export const assistantService = {
  async getAvailableModels(): Promise<AssistantModel[]> {
    const response = await fetch('/api/assistant/available_models');
    if (!response.ok) {
      throw new Error('Failed to fetch available models');
    }
    return response.json();
  },
  async sendMessage(msg: UserMessageRequest): Promise<AssistantResponse> {
    const response = await fetch('/api/assistant/send_message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(msg)
    });
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    return response.json();
  },
  async listSessions(): Promise<AssistantSession[]> {
    const response = await fetch(`/api/assistant/sessions`);
    if (!response.ok) {
      throw new Error('Failed to fetch sessions');
    }
    return response.json();
  }
};

export default assistantService;
