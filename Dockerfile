FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install --yes --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "uv>=0.5"

RUN useradd --create-home --shell /usr/sbin/nologin ausecon
USER ausecon
WORKDIR /home/ausecon

ARG AUSECON_INSTALL_SOURCE=local
ARG AUSECON_VERSION=
COPY --chown=ausecon:ausecon . /home/ausecon/src

RUN if [ "$AUSECON_INSTALL_SOURCE" = "local" ]; then \
      uv tool install /home/ausecon/src; \
    elif [ "$AUSECON_INSTALL_SOURCE" = "pypi" ]; then \
      if [ -z "$AUSECON_VERSION" ]; then \
        echo "AUSECON_VERSION must be set when AUSECON_INSTALL_SOURCE=pypi" >&2; \
        exit 1; \
      fi; \
      uv tool install "ausecon-mcp-server==${AUSECON_VERSION}"; \
    else \
      echo "Unsupported AUSECON_INSTALL_SOURCE: ${AUSECON_INSTALL_SOURCE}" >&2; \
      exit 1; \
    fi

ENV PATH="/home/ausecon/.local/bin:${PATH}"

ENTRYPOINT ["ausecon-mcp-server"]
