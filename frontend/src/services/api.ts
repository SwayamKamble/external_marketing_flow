import axios from "axios";

// If the app is hosted on Vercel but no custom API host is set, default to local loopback (127.0.0.1)
const API_HOST = import.meta.env.VITE_API_HOST || "127.0.0.1";
const API_PORT = import.meta.env.VITE_API_PORT || "8000";

// Force HTTP/WS protocols for local API hosts (like 127.0.0.1, localhost) to avoid SSL handshake errors
// when making calls from HTTPS (Vercel) to local HTTP backend.
const isLocalApi = API_HOST === "127.0.0.1" || API_HOST === "localhost" || API_HOST === "::1";
const API_PROTOCOL = import.meta.env.VITE_API_PROTOCOL || (isLocalApi ? "http" : window.location.protocol.replace(":", "") || "http");

// If hosted on Vercel (production or preview), default to our production backend URL if not set
const DEFAULT_PRODUCTION_BACKEND = "https://external-marketing-flow.vercel.app";
const isHostedOnVercel = typeof window !== "undefined" && window.location.hostname.includes("vercel.app");

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (isHostedOnVercel ? DEFAULT_PRODUCTION_BACKEND : `${API_PROTOCOL}://${API_HOST}:${API_PORT}`);


// Derive WS_BASE_URL from API_BASE_URL if no custom WS URL is provided
const defaultWsBaseUrl = API_BASE_URL.startsWith("https://")
  ? API_BASE_URL.replace("https://", "wss://")
  : API_BASE_URL.replace("http://", "ws://");

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || defaultWsBaseUrl;
const ALT_API_PORT = API_PORT === "8000" ? "8010" : "8000";
const ALT_API_BASE_URL = `${API_PROTOCOL}://${API_HOST}:${ALT_API_PORT}`;

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minute timeout for deep research + content generation
});

// Attach Authorization Bearer token if it exists in local storage
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers = config.headers || {};
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Catch 401 Unauthorized errors to automatically logout and refresh
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_username");
      localStorage.removeItem("auth_user_id");
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

function shouldRetryOnAltPort(err: any): boolean {
  if (!err) return false;
  if (!err.response && (err.code === "ERR_NETWORK" || err.code === "ECONNABORTED")) return true;
  return false;
}

export async function requestWithPortFallback<T>(fn: (client: typeof api) => Promise<T>): Promise<T> {
  try {
    return await fn(api);
  } catch (err: any) {
    // Only attempt to retry on alternate port if it's a local development API
    if (!shouldRetryOnAltPort(err) || !isLocalApi) throw err;
    const altApi = axios.create({ baseURL: ALT_API_BASE_URL, timeout: 300000 });
    try {
      return await fn(altApi as typeof api);
    } catch (altErr: any) {
      const combined = new Error(
        `Network Error: backend unreachable at ${API_BASE_URL} and ${ALT_API_BASE_URL}. Start backend and retry.`
      );
      (combined as any).cause = altErr;
      throw combined;
    }
  }
}

export const startPipeline = async (week_id: string) => {
  console.log("[ContentForge] Starting pipeline for:", week_id);
  const { data } = await requestWithPortFallback((client) =>
    client.post("/pipeline/start", { week_id }, { timeout: 15000 })
  );
  console.log("[ContentForge] Pipeline started:", data);
  return data;
};

export const getPipelineStatus = async (week_id: string) => {
  const { data } = await requestWithPortFallback((client) =>
    client.get(`/pipeline/${week_id}/status`, { timeout: 10000 })
  );
  return data;
};

export const provideFeedback = async (week_id: string, action: string, feedback: string = "", payloadData: any = {}) => {
  console.log("[ContentForge] Providing feedback:", action, payloadData);
  const { data } = await requestWithPortFallback((client) => client.post(`/pipeline/${week_id}/feedback`, {
    action,
    feedback,
    ...payloadData
  }));
  console.log("[ContentForge] Feedback response:", data);
  return data;
};

export const selectTopics = async (week_id: string, topicIds: string[]) => {
  console.log("[ContentForge] Selecting topics:", topicIds);
  const { data } = await requestWithPortFallback((client) => client.post(`/pipeline/${week_id}/feedback`, {
    action: "select_topics",
    selected_topics: topicIds,
  }));
  return data;
};

export const submitDeepResearchForTopic = async (week_id: string, topicId: string, deepResearchText: string) => {
  const { data } = await requestWithPortFallback((client) => client.post(`/pipeline/${week_id}/feedback`, {
    action: "supply_deep_research",
    topic_id: topicId,
    deep_research_text: deepResearchText,
  }));
  return data;
};

export const renderCarouselPreview = async (week_id: string, topicId: string, htmlContent?: string) => {
  const { data } = await requestWithPortFallback((client) => 
    client.post(`/carousel/render/${week_id}/${topicId}`, htmlContent ? { html_content: htmlContent } : {})
  );
  return data;
};

export const getArtifact = async (week_id: string, phase: string, filename: string) => {
  const { data } = await requestWithPortFallback((client) =>
    client.get(`/memory/artifact/${week_id}/${phase}/${filename}`, { timeout: 10000 })
  );
  return data;
};

export const connectWebSocket = (onMessage: (msg: any) => void) => {
  const ws = new WebSocket(`${WS_BASE_URL}/events/ws`);
  
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
