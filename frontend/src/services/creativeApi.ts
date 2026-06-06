import { requestWithPortFallback } from "./api";

export const startCreativeSession = (weekId: string, niche: string = "AI & Tech", topicCount: number = 12) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post("/creative/start", { week_id: weekId, niche, topic_count: topicCount });
    return data;
  });

export const getCreativeStatus = (sessionId: string) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.get(`/creative/${sessionId}/status`);
    return data;
  });

export const submitCreativeResearch = (sessionId: string, rawResearch: string) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post(`/creative/${sessionId}/submit-research`, { raw_research: rawResearch });
    return data;
  });

export const selectCreativeTopics = (sessionId: string, topicIds: string[]) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post(`/creative/${sessionId}/select-topics`, { topic_ids: topicIds });
    return data;
  });

export const planCreativeWeek = (sessionId: string) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post(`/creative/${sessionId}/plan-week`);
    return data;
  });

export const updateCreativePlan = (sessionId: string, planId: number, updates: Record<string, any>) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.put(`/creative/${sessionId}/update-plan`, { plan_id: planId, updates });
    return data;
  });

export const listCreativeSessions = () =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.get("/creative/sessions");
    return data;
  });

// ── Quick Prompt Pipeline (6-step flow) ──

export const startQuickSession = (seriesLength: number, contentFilter: string, userTopic: string = "", platform: string = "instagram") =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post("/creative/quick/start", {
      series_length: seriesLength,
      content_filter: contentFilter,
      user_topic: userTopic,
      platform: platform,
    });
    return data;
  });

export const submitQuickTopics = (sessionId: string, rawJson: string) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post(`/creative/quick/${sessionId}/submit-topics`, { raw_json: rawJson });
    return data;
  });

export const selectQuickTopic = (sessionId: string, topicId: string) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post(`/creative/quick/${sessionId}/select-topic`, { topic_id: topicId });
    return data;
  });

export const submitQuickResearch = (sessionId: string, rawResearch: string) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post(`/creative/quick/${sessionId}/submit-research`, { raw_research: rawResearch });
    return data;
  });

export const chatQuickEdit = (sessionId: string, message: string) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post(`/creative/quick/${sessionId}/chat`, { message });
    return data;
  });

export const approveQuickPlan = (sessionId: string) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post(`/creative/quick/${sessionId}/approve`);
    return data;
  });

export const getQuickStatus = (sessionId: string) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.get(`/creative/quick/${sessionId}/status`);
    return data;
  });

export const listQuickSessions = () =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.get("/creative/quick/sessions");
    return data;
  });

// ── Authentication Endpoints ──

export const signupUser = (username: string, password: string) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post("/creative/auth/signup", { username, password });
    return data;
  });

export const loginUser = (username: string, password: string) =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post("/creative/auth/login", { username, password });
    return data;
  });

export const logoutUser = () =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.post("/creative/auth/logout");
    return data;
  });

export const getCurrentUser = () =>
  requestWithPortFallback(async (client) => {
    const { data } = await client.get("/creative/auth/me");
    return data;
  });
