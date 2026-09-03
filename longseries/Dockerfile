# longseries collector image. One image; one container per source (see compose.yaml).
# Needs NO GPU — collection is I/O and DOM parsing. Runs on the Beelink, a €5 VPS,
# or anything else with Docker, which is the point: collection must survive an
# international relocation. Extraction (the GPU tier) is a separate service.
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir . && python -c "import longseries; print('longseries', longseries.__version__)"
VOLUME ["/data"]
ENTRYPOINT ["python", "-m", "longseries"]
CMD ["--help"]
