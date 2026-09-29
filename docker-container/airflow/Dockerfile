# Use Airflow 2.9.1 with Python 3.11 (explicit tag)
FROM apache/airflow:2.9.1-python3.11

# Switch to root for system dependencies
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Install pinned ML & provider packages
# ATURAN constraints 2.9.1: perintah pip yang bisa mengubah versi core WAJIB
# menyertakan "apache-airflow==X.Y.Z" agar tidak ter-upgrade diam-diam.
# Provider versi kompatibel Airflow 2.9.1 (dari constraints-2.9.1/3.11):
#   postgres==5.10.2, http==4.10.1  (versi 6.x menuntut core 3.x → korup)
RUN pip install --no-cache-dir \
    "apache-airflow==2.9.1" \
    pandas==2.3.3 \
    xgboost==3.2.0 \
    keras==3.14.1 \
    tensorflow==2.21.0 \
    scikit-learn==1.8.0 \
    joblib==1.5.3 \
    pyarrow==24.0.0 \
    "apache-airflow-providers-postgres==5.10.2" \
    "apache-airflow-providers-http==4.10.1" \
    # TF 2.21 butuh protobuf>=6.31.1; OTEL 1.24 membutuhkan protobuf<5 → konflik.
    # Pin keluarga OTEL 1.45.0 (terbukti kompatibel TF 2.21 + protobuf 6.x;
    # memenuhi syarat airflow: opentelemetry-api>=1.15.0):
    "opentelemetry-api==1.45.0" \
    "opentelemetry-sdk==1.45.0" \
    "opentelemetry-proto==1.45.0" \
    "opentelemetry-exporter-otlp-proto-grpc==1.45.0" \
    "opentelemetry-exporter-otlp-proto-http==1.45.0"