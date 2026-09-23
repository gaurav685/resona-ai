import {
  ApiError,
  ContextResponse,
  ExplanationResponse,
  FeedbackResponse,
  FeedbackType,
  ListeningDNA,
  ModelInfoResponse,
  PersonaResponse,
  PersonalityPredictResponse,
  RecommendationsResponse,
  SampleParticipantsResponse,
  SimilarTracksResponse,
  TasteEvolutionResponse,
  UserSummary,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(0, "Could not reach the Resona API. Is the backend running?");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore, keep statusText
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listUsers: () => request<{ users: UserSummary[] }>("/api/v1/users"),

  getListeningDNA: (userId: string) =>
    request<ListeningDNA>(`/api/v1/users/${encodeURIComponent(userId)}/listening-dna`),

  getPersona: (userId: string) =>
    request<PersonaResponse>(`/api/v1/users/${encodeURIComponent(userId)}/persona`),

  getCurrentContext: (userId: string) =>
    request<ContextResponse>(`/api/v1/users/${encodeURIComponent(userId)}/current-context`),

  getTasteEvolution: (userId: string) =>
    request<TasteEvolutionResponse>(`/api/v1/users/${encodeURIComponent(userId)}/taste-evolution`),

  getPersonalityModelInfo: () => request<ModelInfoResponse>("/api/v1/personality/model-info"),

  getSampleParticipants: () =>
    request<SampleParticipantsResponse>("/api/v1/personality/sample-participants"),

  predictPersonality: (features: Record<string, number>) =>
    request<PersonalityPredictResponse>("/api/v1/personality/predict", {
      method: "POST",
      body: JSON.stringify({ features }),
    }),

  getRecommendations: (userId: string, opts: { limit?: number; novelty?: number; context?: string } = {}) => {
    const params = new URLSearchParams({ user_id: userId });
    if (opts.limit !== undefined) params.set("limit", String(opts.limit));
    if (opts.novelty !== undefined) params.set("novelty", String(opts.novelty));
    if (opts.context) params.set("context", opts.context);
    return request<RecommendationsResponse>(`/api/v1/recommendations?${params.toString()}`);
  },

  getExplanation: (recommendationId: string) =>
    request<ExplanationResponse>(`/api/v1/recommendations/${encodeURIComponent(recommendationId)}/explanation`),

  submitFeedback: (recommendationId: string, feedbackType: FeedbackType) =>
    request<FeedbackResponse>(`/api/v1/recommendations/${encodeURIComponent(recommendationId)}/feedback`, {
      method: "POST",
      body: JSON.stringify({ feedback_type: feedbackType }),
    }),

  getSimilarTracks: (trackId: string, limit = 10) =>
    request<SimilarTracksResponse>(
      `/api/v1/tracks/${encodeURIComponent(trackId)}/similar?limit=${limit}`
    ),
};

export { ApiError };
