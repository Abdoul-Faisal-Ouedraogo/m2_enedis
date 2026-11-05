FROM python:3.13.18-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 \
    MPLCONFIGDIR=/tmp/matplotlib ENEDIS_RUNTIME=/app/runtime
WORKDIR /app
COPY requirements-app.txt ./
RUN pip install --no-cache-dir -r requirements-app.txt \
    && useradd --create-home --uid 1000 app \
    && mkdir -p data output runtime && chown app:app runtime
COPY home.py ./
COPY src/ ./src/
COPY assets/ ./assets/
COPY config/preparation_initial_geo_v1.json ./config/preparation_initial_geo_v1.json
COPY .streamlit/ ./.streamlit/
COPY MLmodels/final_models.json ./MLmodels/final_models.json
COPY MLmodels/final_geo_v1/ ./MLmodels/final_geo_v1/
COPY MLmodels/final_geo_v2_temperature/ ./MLmodels/final_geo_v2_temperature/
COPY Notebooks_Api_Traitement/1_data_preparation.ipynb ./Notebooks_Api_Traitement/1_data_preparation.ipynb
COPY scripts/smoke_container.py ./scripts/smoke_container.py
USER app
EXPOSE 8501 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"
CMD ["python", "-m", "streamlit", "run", "home.py", "--server.address=0.0.0.0", "--server.port=8501", "--browser.gatherUsageStats=false"]
