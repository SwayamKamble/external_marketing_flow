import axios from "axios";

// If the app is hosted on Vercel but no custom API host is set, default to local loopback (127.0.0.1)
const API_HOST = import.meta.env.VITE_API_HOST || "127.0.0.1";
const API_PORT = import.meta.env.VITE_API_PORT || "8000";

// Force HTTP protocol for local API hosts (like 127.0.0.1, localhost) to avoid SSL handshake errors
// when making calls from HTTPS (Vercel) to local HTTP backend.
const isLocalApi = API_HOST === "127.0.0.1" || API_HOST === "localhost" || API_HOST === "::1";
const API_PROTOCOL = import.meta.env.VITE_API_PROTOCOL || (isLocalApi ? "http" : window.location.protocol.replace(":", "") || "http");

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || `${API_PROTOCOL}://${API_HOST}:${API_PORT}`;

const client = axios.create({ baseURL: API_BASE_URL, timeout: 60000 });

export const startCreativeSession = async (weekId: string, niche: string = "AI & Tech", topicCount: number = 12) => {
  const { data } = await client.post("/creative/start", { week_id: weekId, niche, topic_count: topicCount });
  return data;
};

export const getCreativeStatus = async (sessionId: string) => {
  const { data } = await client.get(`/creative/${sessionId}/status`);
  return data;
};

export const submitCreativeResearch = async (sessionId: string, rawResearch: string) => {
  const { data } = await client.post(`/creative/${sessionId}/submit-research`, { raw_research: rawResearch });
  return data;
};

export const selectCreativeTopics = async (sessionId: string, topicIds: string[]) => {
  const { data } = await client.post(`/creative/${sessionId}/select-topics`, { topic_ids: topicIds });
  return data;
};

export const planCreativeWeek = async (sessionId: string) => {
  const { data } = await client.post(`/creative/${sessionId}/plan-week`);
  return data;
};

export const updateCreativePlan = async (sessionId: string, planId: number, updates: Record<string, any>) => {
  const { data } = await client.put(`/creative/${sessionId}/update-plan`, { plan_id: planId, updates });
  return data;
};

export const listCreativeSessions = async () => {
  const { data } = await client.get("/creative/sessions");
  return data;
};

// ── Quick Prompt Pipeline (6-step flow) ──

export const startQuickSession = async (seriesLength: number, contentFilter: string, userTopic: string = "", platform: string = "instagram") => {
  const { data } = await client.post("/creative/quick/start", {
    series_length: seriesLength,
    content_filter: contentFilter,
    user_topic: userTopic,
    platform: platform,
  });
  return data;
};

export const submitQuickTopics = async (sessionId: string, rawJson: string) => {
  const { data } = await client.post(`/creative/quick/${sessionId}/submit-topics`, { raw_json: rawJson });
  return data;
};

export const selectQuickTopic = async (sessionId: string, topicId: string) => {
  const { data } = await client.post(`/creative/quick/${sessionId}/select-topic`, { topic_id: topicId });
  return data;
};

export const submitQuickResearch = async (sessionId: string, rawResearch: string) => {
  const { data } = await client.post(`/creative/quick/${sessionId}/submit-research`, { raw_research: rawResearch });
  return data;
};

export const chatQuickEdit = async (sessionId: string, message: string) => {
  const { data } = await client.post(`/creative/quick/${sessionId}/chat`, { message });
  return data;
};

export const approveQuickPlan = async (sessionId: string) => {
  const { data } = await client.post(`/creative/quick/${sessionId}/approve`);
  return data;
};

export const getQuickStatus = async (sessionId: string) => {
  const { data } = await client.get(`/creative/quick/${sessionId}/status`);
  return data;
};

export const listQuickSessions = async () => {
  const { data } = await client.get("/creative/quick/sessions");
  return data;
};
