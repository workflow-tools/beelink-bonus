# longseries collector image. One image; one container per source (see compose.yaml).
# Needs NO GPU — collection is I/O and DOM parsing. Runs on the Beelink, a €5 VPS,
# or anything else with Docker, which is the point: collection must survive an
# international relocation. Extraction (the GPU tier) is a separate service.
#
# Plain build:                 docker build -t longseries:local .
# Extraction image (pymupdf):  docker build --build-arg EXTRAS=extract -t longseries:extract .
# Behind a TLS-intercepting proxy (CI sandboxes; never the Beelink):
#                              docker build --secret id=ca,src=/path/to/proxy-ca.crt -t longseries:local .
# The secret is only visible to that one RUN step and is not stored in the image.
#
# Dependencies come from requirements*.lock (pip-compile, hashes included), so two builds a
# year apart install the same bytes. Regenerate after editing pyproject.toml:
#   pip-compile --generate-hashes --strip-extras -o requirements.lock pyproject.toml
#   pip-compile --generate-hashes --strip-extras --extra extract -o requirements-extract.lock pyproject.toml
FROM python:3.11-slim
ARG EXTRAS=""
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY pyproject.toml requirements.lock requirements-extract.lock ./
COPY src ./src
# hadolint ignore=DL3013
RUN --mount=type=secret,id=ca,required=false \
    if [ -s /run/secrets/ca ]; then export PIP_CERT=/run/secrets/ca; fi; \
    LOCK=requirements.lock; if [ -n "$EXTRAS" ]; then LOCK=requirements-extract.lock; fi; \
    pip install --no-cache-dir --require-hashes -r "$LOCK" \
    && pip install --no-cache-dir --no-deps . \
    && python -c "import longseries; print('longseries', longseries.__version__)" \
    && mkdir -p /data && chown 1000:1000 /data
# Non-root by default. compose overrides `user:` with the data root's real owner (setup
# records it in .env); the one-off `setup` service runs as root so it can chown what it writes.
USER 1000:1000
VOLUME ["/data"]
ENTRYPOINT ["python", "-m", "longseries"]
CMD ["--help"]
