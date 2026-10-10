FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:${PATH}"
ENV XDG_CACHE_HOME=/app/captura_los_santos/cache/xdg XDG_CONFIG_HOME=/tmp/cidade-config LIBGL_ALWAYS_SOFTWARE=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl xz-utils libatomic1 libstdc++6 blender python3-numpy \
    xvfb xauth libgl1-mesa-dri \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv /opt/venv
COPY requirements-runtime.txt /opt/cidade/requirements-runtime.txt
RUN pip install --no-cache-dir -r /opt/cidade/requirements-runtime.txt
# Validar as dependências antes de publicar; esta camada é reutilizada pelo cache.
RUN python -c "import numpy, PIL, szio" \
    && xvfb-run -a blender --background --factory-startup --python-exit-code 1 \
    --python-expr "import bpy, numpy; s=bpy.context.scene; s.render.engine='BLENDER_EEVEE'; s.eevee.taa_render_samples=4; s.render.resolution_x=64; s.render.resolution_y=64; s.render.resolution_percentage=100; bpy.ops.render.render()"
RUN groupadd --gid 10001 cidade && useradd --uid 10001 --gid cidade --create-home cidade \
    && mkdir -p /state /app && chown cidade:cidade /state /app
COPY --chown=cidade:cidade painel_acesso /app/painel_acesso
COPY --chown=cidade:cidade captura_los_santos /app/captura_los_santos
COPY --chown=cidade:cidade server-data /app/server-data
COPY --chown=cidade:cidade servidor-los-santos/server.cfg /app/servidor-los-santos/server.cfg
COPY --chown=cidade:cidade painel_adm_20261009/cayo_thumbnails/native_index.json /app/painel_adm_20261009/cayo_thumbnails/native_index.json
COPY --chown=cidade:cidade laboratorio_fivem/work/assets_index.txt /app/laboratorio_fivem/work/assets_index.txt
COPY --chown=cidade:cidade docker/ /opt/cidade/
RUN mkdir -p /app/painel_acesso/data /app/captura_los_santos/data \
    /app/captura_los_santos/cache /app/server-data/resources/cidade_admin/data \
    && chown -R cidade:cidade /app/painel_acesso/data /app/captura_los_santos/data \
    /app/captura_los_santos/cache /app/server-data/resources/cidade_admin/data
USER cidade
WORKDIR /app
ENTRYPOINT ["python", "/opt/cidade/entrypoint.py"]
