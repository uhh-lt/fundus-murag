import { AgentModel, AgentResponse, AgentSession, UserMessageRequest } from "../types/agentTypes";

export const agentsApiService = {
  async getAvailableModels(): Promise<AgentModel[]> {
    const response = await fetch('/api/agents/available_models');
    if (!response.ok) {
      throw new Error('Failed to fetch available models');
    }
    return response.json();
  },
  async sendMessage(msg: UserMessageRequest): Promise<AgentResponse> {
    const response = await fetch('/api/agents/send_message', {
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
  async listSessions(): Promise<AgentSession[]> {
    const response = await fetch(`/api/agents/sessions`);
    if (!response.ok) {
      throw new Error('Failed to fetch sessions');
    }
    return response.json();
  }
};

export default agentsApiService;
