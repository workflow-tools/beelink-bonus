# longseries collector image. One image; one container per source (see compose.yaml).
# Needs NO GPU — collection is I/O and DOM parsing. Runs on the Beelink, a €5 VPS,
# or anything else with Docker, which is the point: collection must survive an
# international relocation. Extraction (the GPU tier) is a separate service.
#
# Plain build:                 docker build -t longseries:local .
# Extraction image (pymupdf):  docker build --build-arg EXTRAS='[extract]' -t longseries:extract .
# Behind a TLS-intercepting proxy (CI sandboxes; never the Beelink):
#                              docker build --secret id=ca,src=/path/to/proxy-ca.crt -t longseries:local .
# The secret is only visible to that one RUN step and is not stored in the image.
FROM python:3.11-slim
ARG EXTRAS=""
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN --mount=type=secret,id=ca,required=false \
    if [ -s /run/secrets/ca ]; then export PIP_CERT=/run/secrets/ca; fi; \
    pip install --no-cache-dir ".${EXTRAS}" && python -c "import longseries; print('longseries', longseries.__version__)"
VOLUME ["/data"]
ENTRYPOINT ["python", "-m", "longseries"]
CMD ["--help"]
