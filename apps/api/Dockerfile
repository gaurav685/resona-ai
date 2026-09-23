# Builds the API code into a self-sufficient image. Trained model
# artifacts (models/) and datasets (data/) are NOT baked in here — they
# are large and/or gitignored (see DATASETS.md, MODEL_CARD.md) and are
# supplied at runtime via the bind mounts in docker-compose.yml, after
# running the data/training pipeline locally at least once (see README).
FROM python:3.11-slim

WORKDIR /resona/apps/api

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api/app ./app
COPY ml /resona/ml

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
