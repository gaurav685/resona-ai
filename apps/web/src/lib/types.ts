// Mirrors apps/api/app/schemas/*.py response shapes exactly.

export interface UserSummary {
  user_id: string;
  n_events: number;
}

export interface TopArtist {
  artist_name: string;
  play_count: number;
}

export interface ListeningDNA {
  user_id: string;
  n_events: number;
  n_sessions: number;
  top_artists: TopArtist[];
  listening_frequency: number | null;
  average_session_duration_min: number | null;
  tracks_per_session: number | null;
  replay_rate: number | null;
  repeat_rate: number | null;
  artist_diversity: number | null;
  artist_concentration: number | null;
  discovery_rate: number | null;
  night_listening_ratio_utc: number | null;
  weekend_listening_ratio_utc: number | null;
  completion_rate: number | null;
  completion_rate_unavailable_reason: string | null;
  skip_rate: number | null;
  skip_rate_unavailable_reason: string | null;
  genre_diversity: number | null;
  genre_diversity_unavailable_reason: string | null;
  genre_concentration: number | null;
  genre_concentration_unavailable_reason: string | null;
  energy: number | null;
  energy_unavailable_reason: string | null;
  valence: number | null;
  valence_unavailable_reason: string | null;
  danceability: number | null;
  danceability_unavailable_reason: string | null;
  tempo: number | null;
  tempo_unavailable_reason: string | null;
  acousticness: number | null;
  acousticness_unavailable_reason: string | null;
  instrumentalness: number | null;
  instrumentalness_unavailable_reason: string | null;
  speechiness: number | null;
  speechiness_unavailable_reason: string | null;
}

export interface PersonaResponse {
  user_id: string;
  cluster_id: number;
  persona_name: string;
  cluster_size: number;
  pca_coordinates: { x: number; y: number };
  cluster_feature_means: Record<string, number>;
  cluster_feature_z_scores: Record<string, number>;
  algorithm: string;
  model_version: string;
  silhouette_score: number;
}

export interface WindowStats {
  n_events: number;
  artist_diversity: number | null;
  repeat_rate: number | null;
  artist_shift: number | null;
  avg_gap_sec: number | null;
  night_ratio: number | null;
}

export interface ContextResponse {
  user_id: string;
  windows: {
    last_5: WindowStats;
    last_10: WindowStats;
    current_session: WindowStats;
    last_30_min: WindowStats;
  };
  baseline: Partial<WindowStats>;
  shifts: {
    artist_shift: number | null;
    diversity_shift: number | null;
    repeat_shift: number | null;
    night_shift: number | null;
    pace_shift_sec: number | null;
    energy_shift: null;
    energy_shift_unavailable_reason: string;
    valence_shift: null;
    valence_shift_unavailable_reason: string;
    tempo_shift: null;
    tempo_shift_unavailable_reason: string;
    genre_shift: null;
    genre_shift_unavailable_reason: string;
  };
  context_label: string;
  context_explanation: string;
  disclaimer: string;
}

export interface TastePeriod {
  period: string;
  n_events: number;
  unique_artists: number;
  artist_diversity: number | null;
  discovery_rate: number | null;
  listening_frequency: number;
}

export interface TasteEvolutionResponse {
  user_id: string;
  periods: TastePeriod[];
}

export interface ModelInfoResponse {
  model_type: string;
  model_version: string;
  feature_columns: string[];
  trait_columns: string[];
}

export interface SampleParticipant {
  participant_id: string;
  features: Record<string, number>;
  actual_traits: Record<string, number>;
}

export interface SampleParticipantsResponse {
  participants: SampleParticipant[];
  note: string;
}

export interface TraitPrediction {
  trait: string;
  score: number;
  confidence: number | null;
  confidence_note: string | null;
  model_version: string;
  important_features: { feature: string; importance: number }[];
}

export interface PersonalityPredictResponse {
  predictions: TraitPrediction[];
  disclaimer: string;
}

export interface ScoreBreakdown {
  co_listening_similarity: number;
  artist_preference: number;
  context_alignment: number;
  novelty: number;
}

export interface RecommendedItem {
  recommendation_id: string;
  item_id: string;
  artist_name: string;
  track_title: string;
  score: number;
  score_breakdown: ScoreBreakdown;
  popularity: number;
  reason_codes: string[];
  explanation: string;
}

export interface RecommendationsResponse {
  user_id: string;
  context_label: string;
  weights_used: Record<string, number>;
  recommendations: RecommendedItem[];
  note: string;
}

export interface Evidence {
  co_listening_similarity: number;
  artist_preference: number;
  context_alignment: number;
  novelty: number;
  popularity: number;
  is_new_artist: boolean;
  genre_preference: number | null;
  genre_preference_unavailable_reason: string | null;
  energy_match: number | null;
  energy_match_unavailable_reason: string | null;
  personality_signal: number | null;
  personality_signal_unavailable_reason: string | null;
}

export interface ExplanationResponse {
  recommendation_id: string;
  user_id: string;
  item_id: string;
  artist_name: string;
  track_title: string;
  context_label: string;
  evidence: Evidence;
  reason_codes: string[];
  explanation: string;
  model_version: string;
}

export type FeedbackType = "like" | "dislike" | "skip" | "save" | "replay" | "hide";

export interface FeedbackResponse {
  feedback_id: string;
  recommendation_id: string;
  user_id: string;
  feedback_type: FeedbackType;
  note: string;
}

export interface SimilarTrack {
  track_id: string;
  similarity: number;
}

export interface SimilarTracksResponse {
  track_id: string;
  similar_tracks: SimilarTrack[];
  method: string;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}
