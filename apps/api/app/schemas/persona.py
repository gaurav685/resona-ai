from pydantic import BaseModel, ConfigDict


class PCACoordinates(BaseModel):
    x: float
    y: float


class PersonaResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    user_id: str
    cluster_id: int
    persona_name: str
    cluster_size: int
    pca_coordinates: PCACoordinates
    cluster_feature_means: dict[str, float]
    algorithm: str
    model_version: str
    silhouette_score: float
