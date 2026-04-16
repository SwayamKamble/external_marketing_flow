import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

export const startPipeline = async (week_id: string) => {
  const { data } = await api.post("/pipeline/start", { week_id });
  return data;
};

export const getPipelineStatus = async (week_id: string) => {
  const { data } = await api.get(`/pipeline/${week_id}/status`);
  return data;
};

export const provideFeedback = async (week_id: string, action: string, feedback: string = "", payloadData: any = {}) => {
  const { data } = await api.post(`/pipeline/${week_id}/feedback`, {
    action,
    feedback,
    ...payloadData
  });
  return data;
};

export const getArtifact = async (week_id: string, phase: string, filename: string) => {
  const { data } = await api.get(`/memory/artifact/${week_id}/${phase}/${filename}`);
  return data;
};

export const connectWebSocket = (onMessage: (msg: any) => void) => {
  const ws = new WebSocket(`ws://localhost:8000/events/ws`);
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error("WS Parse Error", e);
    }
  };
  
  ws.onclose = () => {
    console.log("WebSocket Disconnected. Reconnecting in 3s...");
    setTimeout(() => connectWebSocket(onMessage), 3000);
  };
  
  return ws;
};
