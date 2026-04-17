FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN pip install --no-cache-dir "uv>=0.5"

RUN useradd --create-home --shell /usr/sbin/nologin ausecon
USER ausecon
WORKDIR /home/ausecon

ARG AUSECON_VERSION
RUN uv tool install --python 3.12 ${AUSECON_VERSION:+ausecon-mcp-server==${AUSECON_VERSION}} ${AUSECON_VERSION:-ausecon-mcp-server}

ENV PATH="/home/ausecon/.local/bin:${PATH}"

ENTRYPOINT ["ausecon-mcp-server"]
