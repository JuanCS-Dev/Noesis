# HCL Analyzer Service

**The Predictive Brain of Maximus AI** - Real ML models for forecasting and anomaly detection.

## Features

- ✅ **Hybrid Anomaly Detection:** SARIMA + Isolation Forest ensemble (Sprint 3)
- ✅ **SARIMA forecasting:** CPU/Memory/GPU predictions (1h, 6h, 24h)
- ✅ **Isolation Forest:** Real-time multivariate anomaly detection
- ✅ **XGBoost:** Failure prediction (10-30min ahead)
- ✅ **Kafka streaming:** Consumes metrics, publishes predictions
- ✅ **Model persistence:** Save/load trained models
- ✅ **Zero mocks:** Real statsmodels, scikit-learn, XGBoost
- ✅ **98% Test Coverage:** Comprehensive unit, integration, and performance tests

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
cp .env.example .env

# Run
python main.py
```

Service runs on **port 8002**

### Docker

```bash
docker build -t hcl-analyzer .
docker run -p 8002:8002 \
  -e KB_API_URL=http://hcl-kb-service:8000 \
  -e KAFKA_BROKERS=kafka:9092 \
  -v $(pwd)/models:/app/models \
  hcl-analyzer
```

## API Endpoints

### GET /health
Health check with model status

```bash
curl http://localhost:8002/health
```

### POST /train/sarima/{metric_name}
Train SARIMA model

```bash
# Train CPU forecaster (uses last 30 days)
curl -X POST "http://localhost:8002/train/sarima/cpu_usage?days=30"

# Train Memory forecaster
curl -X POST "http://localhost:8002/train/sarima/memory_usage?days=30"

# Train GPU forecaster
curl -X POST "http://localhost:8002/train/sarima/gpu_usage?days=30"
```

### GET /predict/sarima/{metric_name}
Get forecast prediction

```bash
# Get 24-hour CPU forecast
curl "http://localhost:8002/predict/sarima/cpu_usage?hours=24"
```

Response:
```json
{
  "metric": "cpu_usage",
  "forecast_hours": 24,
  "prediction": {
    "predictions": [78.5, 79.2, 80.1, ...],
    "lower_bound": [75.1, 76.0, ...],
    "upper_bound": [81.9, 82.4, ...],
    "timestamps": ["2025-10-03T11:00:00Z", ...]
  }
}
```

### POST /train/isolation_forest
Train anomaly detector

```bash
curl -X POST "http://localhost:8002/train/isolation_forest?days=30"
```

### GET /models/status
Get all models status

```bash
curl http://localhost:8002/models/status
```

## Machine Learning Models

### NEW: Hybrid Anomaly Detector (Sprint 3)

**Purpose:** Combined temporal + multivariate anomaly detection
**Architecture:** SARIMA + Isolation Forest with weighted ensemble voting

```
┌──────────────────────────────────────────────────────┐
│              HYBRID ANOMALY DETECTOR                 │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────┐    ┌─────────────────────────┐  │
│  │  SARIMA         │    │  Isolation Forest       │  │
│  │  Forecaster     │    │  Detector               │  │
│  │                 │    │                         │  │
│  │  - Time series  │    │  - Multivariate        │  │
│  │  - Seasonality  │    │  - Feature vectors     │  │
│  │  - Trend        │    │  - Outlier scoring     │  │
│  └────────┬────────┘    └──────────┬──────────────┘  │
│           │                        │                  │
│           │   ┌──────────────┐     │                  │
│           └──►│  Ensemble    │◄────┘                  │
│               │  Arbiter     │                        │
│               │              │                        │
│               │  SARIMA: 40% │                        │
│               │  IsoFor: 60% │                        │
│               └──────┬───────┘                        │
│                      │                                │
│           ┌──────────▼──────────┐                    │
│           │  HybridAnomalyResult │                    │
│           │  - is_anomaly       │                    │
│           │  - source           │                    │
│           │  - weighted_score   │                    │
│           │  - confidence       │                    │
│           │  - explanation      │                    │
│           └─────────────────────┘                    │
└──────────────────────────────────────────────────────┘
```

**Key Features:**
- **Temporal Detection:** SARIMA detects deviations from expected time patterns
- **Multivariate Detection:** Isolation Forest catches unusual feature combinations
- **Source Attribution:** Identifies if anomaly is temporal, multivariate, or both
- **Feature Contributions:** Explains which metrics contributed to detection
- **Online Learning:** Continuous adaptation with `detect_and_update()`
- **Fallback Mechanisms:** Graceful degradation if individual models fail

**Usage:**
```python
from core.models.hybrid_detector import HybridAnomalyDetector, HybridConfig

config = HybridConfig(
    sarima_weight=0.4,
    isolation_weight=0.6,
    ensemble_threshold=0.5,
)

detector = HybridAnomalyDetector(config)
detector.fit(time_series_data, multivariate_data)

result = detector.detect(
    time_series_value=current_cpu,
    feature_vector=[cpu, memory, disk, network, latency, errors],
)

if result.is_anomaly:
    print(f"Anomaly detected! Source: {result.source}")
    print(f"Explanation: {result.explanation}")
```

### 1. SARIMA (Seasonal ARIMA)

**Purpose:** Time-series forecasting for metrics
**Algorithm:** Statsmodels SARIMAX
**Training data:** Minimum 7 days, recommended 30+ days
**Forecast horizon:** 1-24 hours

**Parameters:**
- Order (p, d, q) = (1, 1, 1) - ARIMA components
- Seasonal order (P, D, Q, s) = (1, 1, 1, 24) - 24-hour seasonality

**Metrics:**
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- MAPE (Mean Absolute Percentage Error)
- AIC/BIC (Model selection)

**Use case:** Predict CPU/Memory/GPU spikes 1-24h in advance

### 2. Isolation Forest

**Purpose:** Anomaly detection in multi-dimensional metrics
**Algorithm:** sklearn IsolationForest
**Training data:** Normal behavior (30+ days recommended)
**Detection:** Real-time scoring on streaming data

**Parameters:**
- Contamination = 0.01 (expect 1% anomalies)
- N estimators = 100 trees
- Max samples = 'auto'

**Features:**
- Current metrics (CPU, Memory, GPU, latency, errors)
- Rolling statistics (5-period mean/std)
- Time features (hour, day of week)

**Use case:** Detect unusual patterns indicating attacks or failures

### 3. XGBoost Classifier

**Purpose:** Failure prediction
**Algorithm:** XGBoost binary classifier
**Training data:** Historical failures (labeled dataset)
**Prediction window:** 10-30 minutes ahead

**Parameters:**
- N estimators = 100
- Max depth = 5
- Learning rate = 0.1
- Scale pos weight = auto (handles class imbalance)

**Features:**
- Current metrics
- Trend features (rate of change)
- Rolling statistics
- Time features
- Error rate patterns

**Metrics:**
- AUC-ROC (Area Under Curve)
- Precision (avoid false alarms)
- Recall (catch all failures)

**Use case:** Predict service crashes before they happen

### 4. MLSystemAnalyzer (Sprint 3)

**Purpose:** High-level analyzer integrating hybrid detection
**Architecture:** Wraps HybridAnomalyDetector with business logic

**Usage:**
```python
from core.ml_analyzer import MLSystemAnalyzer
from config import AnalyzerSettings

settings = AnalyzerSettings()
analyzer = MLSystemAnalyzer(settings)

# Train on historical data
analyzer.train(historical_metrics)

# Analyze current metrics
result = await analyzer.analyze_metrics(current_metrics)

print(f"Health Score: {result.overall_health_score}")
print(f"Anomalies: {len(result.anomalies)}")
print(f"Trends: {result.trends}")
print(f"Recommendations: {result.recommendations}")
```

**Features:**
- Automatic training from `SystemMetrics` objects
- Health score calculation (0.0 - 1.0)
- Trend identification (increasing, decreasing, stable)
- Actionable recommendations
- Fallback to static thresholds when not trained

## Architecture

```
┌───────────────────────────────┐
│   Kafka: system.telemetry.raw │  (from Monitor)
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│   HCL Analyzer Service        │
│   ┌─────────────────────────┐ │
│   │  Kafka Consumer Loop    │ │
│   └────────┬────────────────┘ │
│            ▼                  │
│   ┌─────────────────────────┐ │
│   │  AnalysisEngine         │ │
│   │  - Buffer metrics       │ │
│   │  - Run models           │ │
│   └────────┬────────────────┘ │
│            ▼                  │
│   ┌─────────────────────────┐ │
│   │  ModelRegistry          │ │
│   │  - SARIMA (3x)          │ │
│   │  - Isolation Forest     │ │
│   │  - XGBoost              │ │
│   └────────┬────────────────┘ │
└────────────┼──────────────────┘
             │
             ▼
┌───────────────────────────────┐
│   Kafka: system.predictions   │  (to Planner)
└───────────────────────────────┘
```

## Training Pipeline

### Initial Training

1. **Fetch historical data** from Knowledge Base (30+ days)
2. **Train each model** independently
3. **Save models** to disk (/app/models/)
4. **Validate** on held-out test set
5. **Deploy** (mark as loaded)

### Continuous Learning

- **Scheduled retraining:** Daily via Airflow DAG
- **Incremental updates:** Online learning for some models
- **Model versioning:** Track performance over time
- **A/B testing:** Compare new vs old models

## Kafka Topics

### Consumes
- `system.telemetry.raw` - Raw metrics from Monitor

### Produces
- `system.predictions` - Forecasts and anomalies

**Prediction message format:**
```json
{
  "type": "anomaly_detection",
  "timestamp": "2025-10-03T10:30:00Z",
  "n_anomalies": 3,
  "details": {
    "timestamps": [...],
    "anomaly_scores": [...],
    "is_anomaly": [true, false, true, ...]
  }
}
```

## Performance

- **Inference latency:** <100ms per prediction
- **Training time:**
  - SARIMA: 2-5 minutes (30 days data)
  - Isolation Forest: 30-60 seconds
  - XGBoost: 1-2 minutes
- **Memory:** <1GB RSS
- **CPU:** <10% usage (inference), 50-100% (training)

## Production Deployment

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hcl-analyzer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hcl-analyzer
  template:
    metadata:
      labels:
        app: hcl-analyzer
    spec:
      containers:
      - name: hcl-analyzer
        image: hcl-analyzer:latest
        env:
        - name: KB_API_URL
          value: "http://hcl-kb-service:8000"
        - name: KAFKA_BROKERS
          value: "kafka:9092"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        volumeMounts:
        - name: models
          mountPath: /app/models
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: hcl-models-pvc
```

## Model Persistence

Models are saved to disk and loaded on startup:

```
/app/models/
├── sarima_cpu.pkl
├── sarima_memory.pkl
├── sarima_gpu.pkl
├── isolation_forest.pkl
└── xgboost_failure.pkl
```

**Volume mount recommended for production.**

## Testing

### Running Tests

```bash
# Run all tests with coverage
PYTHONPATH=. python -m pytest tests/ -v --cov=core --cov-report=term-missing

# Run specific test categories
PYTHONPATH=. python -m pytest tests/test_integration.py -v  # Integration tests
PYTHONPATH=. python -m pytest tests/test_hybrid_detector.py -v  # Hybrid detector tests
PYTHONPATH=. python -m pytest tests/test_ml_analyzer.py -v  # ML analyzer tests
```

### Test Coverage (98%)

| Module | Coverage |
|--------|----------|
| `core/analyzer.py` | 100% |
| `core/ml_analyzer.py` | 99% |
| `core/models/hybrid_detector.py` | 100% |
| `core/models/isolation_detector.py` | 95% |
| `core/models/sarima_forecaster.py` | 91% |

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Full pipeline testing
- **Performance Benchmarks**: Training and inference timing
- **Edge Cases**: Boundary conditions and error handling

### Performance Benchmarks

| Operation | Time |
|-----------|------|
| SARIMA Training (200 points) | < 5s |
| SARIMA Prediction | < 50ms |
| Isolation Forest Training (500 points) | < 2s |
| Isolation Forest Detection | < 100ms |
| Hybrid Detection (full pipeline) | < 200ms |
| ML Analyzer Analysis | < 100ms |

## Zero Mock Guarantee

- ✅ Real **statsmodels SARIMAX** (ARIMA forecasting)
- ✅ Real **scikit-learn IsolationForest**
- ✅ Real **XGBoost** gradient boosting
- ✅ Real **pandas DataFrame** operations
- ✅ Real **Kafka consumer/producer**
- ✅ Real **model persistence** (pickle/joblib)

**Production-ready ML code. No placeholders.**

---

## 📦 Dependency Management

This service follows **strict dependency governance** to ensure security, stability, and reproducibility.

### Quick Reference

**Check for vulnerabilities**:
```bash
bash scripts/dependency-audit.sh
```

**Add new dependency**:
```bash
echo "package==1.2.3" >> requirements.txt
pip-compile requirements.txt --output-file requirements.txt.lock
bash scripts/dependency-audit.sh  # Verify no CVEs
git add requirements.txt requirements.txt.lock
git commit -m "feat: add package for feature X"
```

### Policies & SLAs

📋 **[DEPENDENCY_POLICY.md](./DEPENDENCY_POLICY.md)** - Complete policy documentation

**Key SLAs**:
- **CRITICAL (CVSS >= 9.0)**: 24 hours
- **HIGH (CVSS >= 7.0)**: 72 hours
- **MEDIUM (CVSS >= 4.0)**: 2 weeks
- **LOW (CVSS < 4.0)**: 1 month

### Available Scripts

| Script | Purpose |
|--------|---------|
| `dependency-audit.sh` | Full CVE scan |
| `check-cve-whitelist.sh` | Validate whitelist |
| `audit-whitelist-expiration.sh` | Check expired CVEs |
| `generate-dependency-metrics.sh` | Generate metrics JSON |

See [Active Immune Core README](../active_immune_core/README.md#-dependency-management) for complete documentation.

