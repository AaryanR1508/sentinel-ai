"""LLM Safety Gateway API — CPU-centric real-time safety gateway running 3 parallel detection layers with weighted scoring."""

import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from enum import Enum

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Import all layer classes
from utils.reg import SemanticSanitizer
from utils.security_model import SecurityClassifier
from utils.sanitizer import PromptSanitizer
from utils.vector_db import BottleneckExtractor
from utils.cache import AnalysisCache


# =============================================================================
# CONFIGURATION
# =============================================================================


class GatewayConfig:
    """Configuration for the safety gateway."""

    # Layer weights (must sum to 1.0), overridable per request. Regex=fast tripwire, Model=50k fine-tuned (highest signal), VectorDB=50k signatures two-pass search.
    WEIGHT_REGEX = 0.10
    WEIGHT_SECURITY_MODEL = 0.55
    WEIGHT_VECTOR_DB = 0.35

    # Thresholds: BLOCK lowered 0.75->0.65 since regex max contribution dropped 0.20->0.10.
    THRESHOLD_PASS = 0.35       # Below this: PASS (safe)
    THRESHOLD_SANITIZE = 0.65   # Below this: SANITIZE, Above: BLOCK


class Action(str, Enum):
    """Possible actions for a prompt."""

    PASS = "pass"
    SANITIZE = "sanitize"
    BLOCK = "block"


# =============================================================================
# PYDANTIC MODELS
# =============================================================================


class WeightsConfig(BaseModel):
    """Custom weights configuration."""

    regex_analyzer: float = GatewayConfig.WEIGHT_REGEX
    security_model: float = GatewayConfig.WEIGHT_SECURITY_MODEL
    vector_db: float = GatewayConfig.WEIGHT_VECTOR_DB


class PromptRequest(BaseModel):
    """Request model for prompt analysis."""

    prompt: str = Field(..., min_length=1, description="The prompt to analyze")
    weights: Optional[WeightsConfig] = None  # Custom weights per request


class LayerScore(BaseModel):
    """Score from a single layer with latency."""

    name: str
    score: float
    weight: float
    weighted_score: float
    latency_ms: float


class AnalysisResponse(BaseModel):
    """Response model for prompt analysis."""

    prompt_preview: str
    action: Action
    weighted_score: float
    layer_scores: list[LayerScore]
    sanitized_prompt: Optional[str] = None
    total_latency_ms: float
    sanitizer_latency_ms: Optional[float] = None
    original_latency_ms: Optional[float] = None  # Set on cache hits; the latency of the original uncached run.
    cache_hit: bool = False


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    layers_loaded: dict[str, bool]


# =============================================================================
# APPLICATION LIFESPAN (Model Initialization)
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all models at startup and clean up on shutdown."""
    print("\n" + "=" * 60)
    print("🚀 LLM SAFETY GATEWAY - INITIALIZING")
    print("=" * 60 + "\n")

    # Store layer instances in app state
    try:
        # Layer 1: Regex Analyzer
        print("📦 Loading Layer 1: Regex Analyzer...")
        app.state.regex_layer = SemanticSanitizer()

        # Layer 2: Security Model (Transformer Classifier)
        print("\n📦 Loading Layer 2: Security Model...")
        app.state.security_model = SecurityClassifier()

        # Layer 3: Vector DB (Semantic similarity to jailbreaks)
        print("\n📦 Loading Layer 3: Vector DB (Bottleneck Extractor)...")
        app.state.vector_db_layer = BottleneckExtractor()

        # Sanitizer Layer (only used when needed)
        print("\n📦 Loading Sanitizer Layer...")
        try:
            app.state.sanitizer = PromptSanitizer()
            app.state.sanitizer_available = True
        except ValueError as e:
            print(f"[!] Warning: {e}")
            print(
                "[!] Sanitizer will not be available - prompts requiring sanitization will be blocked."
            )
            app.state.sanitizer = None
            app.state.sanitizer_available = False

        # Semantic Cache (for repeated prompts)
        print("\n📦 Loading Semantic Cache...")
        try:
            app.state.analysis_cache = AnalysisCache()
            app.state.cache_available = True
            print("[*] Cache stats endpoint available at GET /cache/stats")
        except Exception as e:
            print(f"[!] Warning: Failed to initialize cache: {e}")
            print("[!] Cache will not be available.")
            app.state.analysis_cache = None
            app.state.cache_available = False

        print("\n" + "=" * 60)
        print("✅ ALL LAYERS LOADED SUCCESSFULLY")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ FATAL: Failed to initialize layers: {e}")
        raise

    yield  # Server runs here

    # Cleanup (if needed)
    print("\n🛑 Shutting down LLM Safety Gateway...")


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="LLM Safety Gateway",
    description="CPU-centric, lightweight real-time safety gateway for LLM prompts",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


async def run_all_layers(
    prompt: str, app_state, weights: WeightsConfig
) -> tuple[list[LayerScore], float]:
    """Run all 3 detection layers in parallel and return (layer_scores, total_latency_ms)."""

    regex_weight = weights.regex_analyzer
    security_weight = weights.security_model

    async def run_regex():
        start = time.perf_counter()
        score = await app_state.regex_layer.get_score_async(prompt)
        latency = (time.perf_counter() - start) * 1000
        return LayerScore(
            name="regex_analyzer",
            score=round(score, 4),
            weight=round(regex_weight, 4),
            weighted_score=round(score * regex_weight, 4),
            latency_ms=round(latency, 2),
        )

    async def run_security_model():
        start = time.perf_counter()
        result = await app_state.security_model.get_score_async(prompt)
        latency = (time.perf_counter() - start) * 1000
        if result["is_dangerous"]:
            score = result["confidence"]
        else:
            score = 1.0 - result["confidence"]
        return LayerScore(
            name="security_model",
            score=round(score, 4),
            weight=round(security_weight, 4),
            weighted_score=round(score * security_weight, 4),
            latency_ms=round(latency, 2),
        )

    async def run_vector_db():
        start = time.perf_counter()
        score = await app_state.vector_db_layer.get_score_async(prompt)
        latency = (time.perf_counter() - start) * 1000
        return LayerScore(
            name="vector_db",
            score=round(score, 4),
            weight=round(weights.vector_db, 4),
            weighted_score=round(score * weights.vector_db, 4),
            latency_ms=round(latency, 2),
        )

    start_total = time.perf_counter()
    results = await asyncio.gather(run_regex(), run_security_model(), run_vector_db())
    total_latency = (time.perf_counter() - start_total) * 1000

    return list(results), round(total_latency, 2)


def determine_action(weighted_score: float) -> Action:
    """Determine action based on weighted score and thresholds."""
    if weighted_score < GatewayConfig.THRESHOLD_PASS:
        return Action.PASS
    elif weighted_score < GatewayConfig.THRESHOLD_SANITIZE:
        return Action.SANITIZE
    else:
        return Action.BLOCK


def get_weights(request_weights: Optional[WeightsConfig]) -> WeightsConfig:
    """Get weights from request or use defaults."""
    if request_weights:
        return request_weights
    return WeightsConfig()


# =============================================================================
# API ENDPOINTS
# =============================================================================


@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Frontend not found. API is running at /docs"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if all layers are loaded and ready."""
    return HealthResponse(
        status="healthy",
        layers_loaded={
            "regex_analyzer": hasattr(app.state, "regex_layer"),
            "security_model": hasattr(app.state, "security_model"),
            "vector_db": hasattr(app.state, "vector_db_layer"),
            "sanitizer": getattr(app.state, "sanitizer_available", False),
        },
    )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_prompt(request: PromptRequest):
    """Analyze a prompt through all safety layers without sanitizing and return scores/action."""
    prompt = request.prompt
    weights = get_weights(request.weights)
    cached_response = None
    cache_start = time.perf_counter()

    # Check cache first
    if getattr(app.state, "cache_available", False):
        try:
            cached = await app.state.analysis_cache.get(prompt)
            if cached:
                cached_response = cached
        except Exception as e:
            print(f"[!] Cache check failed: {e}")

    if cached_response:
        cache_latency = round((time.perf_counter() - cache_start) * 1000, 2)
        zeroed_layers = [LayerScore(**{**ls, "latency_ms": 0.0}) for ls in cached_response["layer_scores"]]
        return AnalysisResponse(
            prompt_preview=prompt[:512] + "..." if len(prompt) > 512 else prompt,
            action=Action(cached_response["action"]),
            weighted_score=cached_response["weighted_score"],
            layer_scores=zeroed_layers,
            sanitized_prompt=cached_response.get("sanitized_prompt"),
            total_latency_ms=cache_latency,
            original_latency_ms=cached_response.get("original_latency_ms"),
            cache_hit=True,
        )

    # Run all layers in parallel
    layer_scores, total_latency = await run_all_layers(prompt, app.state, weights)

    # Calculate weighted score
    weighted_score = sum(layer.weighted_score for layer in layer_scores)

    # Determine action
    action = determine_action(weighted_score)

    # Build response to cache — latency is NOT cached; original_latency_ms stored for cache-hit comparison.
    response_data = {
        "action": action.value,
        "weighted_score": round(weighted_score, 4),
        "layer_scores": [ls.model_dump() for ls in layer_scores],
        "sanitized_prompt": None,
        "original_latency_ms": total_latency,
    }

    # Store in cache
    if getattr(app.state, "cache_available", False):
        try:
            await app.state.analysis_cache.store(prompt, response_data)
        except Exception as e:
            print(f"[!] Cache store failed: {e}")

    return AnalysisResponse(
        prompt_preview=prompt[:512] + "..." if len(prompt) > 512 else prompt,
        action=action,
        weighted_score=round(weighted_score, 4),
        layer_scores=layer_scores,
        sanitized_prompt=None,
        total_latency_ms=total_latency,
        cache_hit=False,
    )


@app.post("/gateway", response_model=AnalysisResponse)
async def gateway(request: PromptRequest):
    """Full gateway pipeline: check cache, run layers in parallel, score, decide PASS/SANITIZE/BLOCK, cache result."""
    prompt = request.prompt
    weights = get_weights(request.weights)
    cached_response = None
    cache_start = time.perf_counter()

    # Check cache first
    if getattr(app.state, "cache_available", False):
        try:
            cached = await app.state.analysis_cache.get(prompt)
            if cached:
                cached_response = cached
        except Exception as e:
            print(f"[!] Cache check failed: {e}")

    if cached_response:
        cache_latency = round((time.perf_counter() - cache_start) * 1000, 2)
        zeroed_layers = [LayerScore(**{**ls, "latency_ms": 0.0}) for ls in cached_response["layer_scores"]]
        return AnalysisResponse(
            prompt_preview=prompt[:512] + "..." if len(prompt) > 512 else prompt,
            action=Action(cached_response["action"]),
            weighted_score=cached_response["weighted_score"],
            layer_scores=zeroed_layers,
            sanitized_prompt=cached_response.get("sanitized_prompt"),
            total_latency_ms=cache_latency,
            original_latency_ms=cached_response.get("original_latency_ms"),
            cache_hit=True,
        )

    # Run all layers in parallel
    layer_scores, total_latency = await run_all_layers(prompt, app.state, weights)

    # Calculate weighted score
    weighted_score = sum(layer.weighted_score for layer in layer_scores)

    # Determine action
    action = determine_action(weighted_score)

    # Handle sanitization if needed
    sanitized_prompt = None
    sanitizer_latency = None
    if action == Action.SANITIZE:
        if app.state.sanitizer_available:
            try:
                start = time.perf_counter()
                sanitized_prompt = await app.state.sanitizer.sanitize_async(prompt)
                sanitizer_latency = round((time.perf_counter() - start) * 1000, 2)
            except Exception as e:
                print(f"[!] Sanitization failed: {e}")
                action = Action.BLOCK
        else:
            action = Action.BLOCK

    # Build response to cache — latency is NOT cached; original_latency_ms stored for cache-hit comparison.
    response_data = {
        "action": action.value,
        "weighted_score": round(weighted_score, 4),
        "layer_scores": [ls.model_dump() for ls in layer_scores],
        "sanitized_prompt": sanitized_prompt,
        "original_latency_ms": total_latency + (sanitizer_latency or 0),
    }

    # Store in cache
    if getattr(app.state, "cache_available", False):
        try:
            await app.state.analysis_cache.store(prompt, response_data)
        except Exception as e:
            print(f"[!] Cache store failed: {e}")

    return AnalysisResponse(
        prompt_preview=prompt[:512] + "..." if len(prompt) > 512 else prompt,
        action=action,
        weighted_score=round(weighted_score, 4),
        layer_scores=layer_scores,
        sanitized_prompt=sanitized_prompt,
        total_latency_ms=total_latency + (sanitizer_latency or 0),
        sanitizer_latency_ms=sanitizer_latency,
        cache_hit=False,
    )


@app.get("/config")
async def get_config():
    """Get current gateway configuration (weights and thresholds)."""
    return {
        "weights": {
            "regex_analyzer": GatewayConfig.WEIGHT_REGEX,
            "security_model": GatewayConfig.WEIGHT_SECURITY_MODEL,
            "vector_db": GatewayConfig.WEIGHT_VECTOR_DB,
        },
        "thresholds": {
            "pass": GatewayConfig.THRESHOLD_PASS,
            "sanitize": GatewayConfig.THRESHOLD_SANITIZE,
        },
        "actions": {
            "score < threshold_pass": "PASS (safe, forward to LLM)",
            "threshold_pass <= score < threshold_sanitize": "SANITIZE (clean before forwarding)",
            "score >= threshold_sanitize": "BLOCK (reject entirely)",
        },
    }


@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache performance statistics."""
    if not getattr(app.state, "cache_available", False):
        return {"status": "unavailable", "message": "Cache is not enabled"}

    try:
        stats = app.state.analysis_cache.get_stats()
        return {"status": "healthy", "cache": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
