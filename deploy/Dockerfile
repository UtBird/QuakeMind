FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
    HF_HOME=/app/veri/huggingface NLTK_DATA=/usr/local/share/nltk_data
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 libgl1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && python -m nltk.downloader -d /usr/local/share/nltk_data stopwords punkt punkt_tab \
    && pip check
RUN useradd --uid 10001 --create-home app
ARG BACKEND_DIR=backend
WORKDIR /app/${BACKEND_DIR}
COPY --chown=app:app source/ ./
COPY --chown=app:app legacy-tools/ /app/quakemind/tool/
RUN mkdir -p veri apps/road_damage/models apps/disaster_nlp/models /home/app/.cache \
    && python araclar_risk_egit.py \
    && chown -R app:app /app /home/app
USER app
HEALTHCHECK --interval=15s --timeout=5s --start-period=240s --retries=4 \
    CMD python -c "import json,urllib.request; assert json.load(urllib.request.urlopen('http://127.0.0.1:8000/',timeout=4))['status']=='ok'"
CMD ["python", "-m", "uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
