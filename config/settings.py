"""
Configuration settings for AI Video Editor
Load from environment variables with sensible defaults
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# PROJECT PATHS
# ============================================================================

# Base directories
BASE_DIR = Path(__file__).parent.parent
PROJECTS_DIR = BASE_DIR / "projects"
DATABASE_DIR = BASE_DIR / "database"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
PROJECTS_DIR.mkdir(exist_ok=True)
DATABASE_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ============================================================================
# API KEYS
# ============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

# Vision Model
VISION_MODEL = os.getenv("VISION_MODEL", "gpt-4o")
VISION_MAX_TOKENS = int(os.getenv("VISION_MAX_TOKENS", "300"))
VISION_DETAIL = os.getenv("VISION_DETAIL", "high")  # "low" | "high" | "auto"

# Analysis Model (can use GPT-4o or Claude)
ANALYSIS_MODEL = os.getenv("ANALYSIS_MODEL", "gpt-4o")

# Text-to-Speech
TTS_MODEL = os.getenv("TTS_MODEL", "tts-1-hd")  # "tts-1" or "tts-1-hd"
TTS_VOICE = os.getenv("TTS_VOICE", "alloy")  # alloy, echo, fable, onyx, nova, shimmer
TTS_SPEED = float(os.getenv("TTS_SPEED", "1.0"))  # 0.25 to 4.0

# Whisper Model
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")

# Cursor Detection
CURSOR_MODEL = os.getenv("CURSOR_MODEL", "yolov8")  # "yolov8" or "roboflow"
YOLO_MODEL_SIZE = os.getenv("YOLO_MODEL_SIZE", "n")  # n, s, m, l, x (nano to xlarge)
CURSOR_CONFIDENCE_THRESHOLD = float(os.getenv("CURSOR_CONFIDENCE_THRESHOLD", "0.7"))

# ============================================================================
# FRAME EXTRACTION SETTINGS
# ============================================================================

DEFAULT_FPS = float(os.getenv("DEFAULT_FPS", "2.5"))
MAX_FRAMES = int(os.getenv("MAX_FRAMES", "500"))
FRAME_RESOLUTION = os.getenv("FRAME_RESOLUTION", "1280x720")
FRAME_FORMAT = os.getenv("FRAME_FORMAT", "jpg")
FRAME_QUALITY = int(os.getenv("FRAME_QUALITY", "85"))  # JPEG quality 1-100

# ============================================================================
# VISION ANALYSIS SETTINGS
# ============================================================================

FRAME_SAMPLE_RATE = int(os.getenv("FRAME_SAMPLE_RATE", "5"))  # Analyze every Nth frame

# ============================================================================
# CURSOR DETECTION SETTINGS
# ============================================================================

CLICK_DETECTION_THRESHOLD = float(os.getenv("CLICK_DETECTION_THRESHOLD", "10.0"))
HOVER_DETECTION_THRESHOLD = float(os.getenv("HOVER_DETECTION_THRESHOLD", "0.5"))  # seconds

# ============================================================================
# AUDIO PROCESSING SETTINGS
# ============================================================================

SILENCE_THRESHOLD_DB = int(os.getenv("SILENCE_THRESHOLD_DB", "-40"))
MIN_SILENCE_DURATION = float(os.getenv("MIN_SILENCE_DURATION", "0.5"))  # seconds

# ============================================================================
# VIDEO RENDERING SETTINGS
# ============================================================================

# Video Encoding
VIDEO_CODEC = os.getenv("VIDEO_CODEC", "libx264")
VIDEO_PRESET = os.getenv("VIDEO_PRESET", "medium")  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
VIDEO_CRF = int(os.getenv("VIDEO_CRF", "23"))  # Constant Rate Factor: 0-51 (lower = better quality)
VIDEO_BITRATE = os.getenv("VIDEO_BITRATE", "8000k")
OUTPUT_FPS = int(os.getenv("OUTPUT_FPS", "30"))

# Audio Encoding
AUDIO_CODEC = os.getenv("AUDIO_CODEC", "aac")
AUDIO_BITRATE = os.getenv("AUDIO_BITRATE", "192k")

# ============================================================================
# API PRICING (USD)
# ============================================================================

# OpenAI GPT-4o
COST_GPT4O_INPUT = 0.0025 / 1000   # $2.50 per 1M input tokens
COST_GPT4O_OUTPUT = 0.01 / 1000     # $10.00 per 1M output tokens

# OpenAI GPT-4o Vision (includes image tokens)
COST_GPT4O_VISION_INPUT = 0.0025 / 1000
COST_GPT4O_VISION_OUTPUT = 0.01 / 1000

# OpenAI Whisper
COST_WHISPER = 0.006  # $0.006 per minute

# OpenAI TTS
COST_TTS = 0.015 / 1000  # $0.015 per 1000 characters (tts-1)
COST_TTS_HD = 0.030 / 1000  # $0.030 per 1000 characters (tts-1-hd)

# Anthropic Claude (if using)
COST_CLAUDE_SONNET_INPUT = 0.003 / 1000
COST_CLAUDE_SONNET_OUTPUT = 0.015 / 1000

# ============================================================================
# API RETRY SETTINGS
# ============================================================================

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))  # seconds

# ============================================================================
# PROJECT MANAGEMENT
# ============================================================================

PROJECT_RETENTION_DAYS = int(os.getenv("PROJECT_RETENTION_DAYS", "30"))
MAX_CONCURRENT_PROJECTS = int(os.getenv("MAX_CONCURRENT_PROJECTS", "3"))

# ============================================================================
# DATABASE SETTINGS
# ============================================================================

DATABASE_PATH = DATABASE_DIR / "projects.db"
DATABASE_BACKUP_ENABLED = os.getenv("DATABASE_BACKUP_ENABLED", "true").lower() == "true"
DATABASE_BACKUP_INTERVAL_HOURS = int(os.getenv("DATABASE_BACKUP_INTERVAL_HOURS", "24"))

# ============================================================================
# LOGGING SETTINGS
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = LOGS_DIR / "video_editor.log"
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

# Enable GPU acceleration if available
USE_GPU = os.getenv("USE_GPU", "auto")  # "auto", "cuda", "cpu"

# Number of worker threads for parallel processing
WORKER_THREADS = int(os.getenv("WORKER_THREADS", "4"))

# ============================================================================
# FEATURE FLAGS
# ============================================================================

ENABLE_CURSOR_DETECTION = os.getenv("ENABLE_CURSOR_DETECTION", "true").lower() == "true"
ENABLE_AUDIO_ANALYSIS = os.getenv("ENABLE_AUDIO_ANALYSIS", "true").lower() == "true"
ENABLE_VISION_ANALYSIS = os.getenv("ENABLE_VISION_ANALYSIS", "true").lower() == "true"
ENABLE_AUTO_EDITS = os.getenv("ENABLE_AUTO_EDITS", "true").lower() == "true"

# ============================================================================
# DEVELOPMENT SETTINGS
# ============================================================================

DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
SAVE_INTERMEDIATE_FILES = os.getenv("SAVE_INTERMEDIATE_FILES", "true").lower() == "true"

# ============================================================================
# VALIDATION
# ============================================================================

def validate_settings():
    """Validate critical settings"""
    issues = []
    
    if not OPENAI_API_KEY:
        issues.append("OPENAI_API_KEY not set")
    
    if DEFAULT_FPS <= 0 or DEFAULT_FPS > 10:
        issues.append(f"DEFAULT_FPS must be between 0 and 10, got {DEFAULT_FPS}")
    
    if MAX_FRAMES < 50:
        issues.append(f"MAX_FRAMES should be at least 50, got {MAX_FRAMES}")
    
    if VIDEO_CRF < 0 or VIDEO_CRF > 51:
        issues.append(f"VIDEO_CRF must be between 0 and 51, got {VIDEO_CRF}")
    
    return issues

# Validate on import
_validation_issues = validate_settings()
if _validation_issues and not DEBUG_MODE:
    import warnings
    for issue in _validation_issues:
        warnings.warn(f"Configuration issue: {issue}")

# ============================================================================
# EXPORT ALL SETTINGS
# ============================================================================

__all__ = [
    # Paths
    'BASE_DIR', 'PROJECTS_DIR', 'DATABASE_DIR', 'MODELS_DIR', 'LOGS_DIR',
    
    # API Keys
    'OPENAI_API_KEY', 'ROBOFLOW_API_KEY', 'ANTHROPIC_API_KEY',
    
    # Models
    'VISION_MODEL', 'VISION_MAX_TOKENS', 'VISION_DETAIL',
    'ANALYSIS_MODEL', 'TTS_MODEL', 'TTS_VOICE', 'TTS_SPEED',
    'WHISPER_MODEL', 'WHISPER_LANGUAGE',
    'CURSOR_MODEL', 'YOLO_MODEL_SIZE', 'CURSOR_CONFIDENCE_THRESHOLD',
    
    # Frame Extraction
    'DEFAULT_FPS', 'MAX_FRAMES', 'FRAME_RESOLUTION', 'FRAME_FORMAT', 'FRAME_QUALITY',
    
    # Vision Analysis
    'FRAME_SAMPLE_RATE',
    
    # Cursor Detection
    'CLICK_DETECTION_THRESHOLD', 'HOVER_DETECTION_THRESHOLD',
    
    # Audio Processing
    'SILENCE_THRESHOLD_DB', 'MIN_SILENCE_DURATION',
    
    # Video Rendering
    'VIDEO_CODEC', 'VIDEO_PRESET', 'VIDEO_CRF', 'VIDEO_BITRATE', 'OUTPUT_FPS',
    'AUDIO_CODEC', 'AUDIO_BITRATE',
    
    # Pricing
    'COST_GPT4O_INPUT', 'COST_GPT4O_OUTPUT', 'COST_WHISPER', 'COST_TTS', 'COST_TTS_HD',
    'COST_CLAUDE_SONNET_INPUT', 'COST_CLAUDE_SONNET_OUTPUT',
    
    # API Settings
    'MAX_RETRIES', 'RETRY_DELAY',
    
    # Project Management
    'PROJECT_RETENTION_DAYS', 'MAX_CONCURRENT_PROJECTS',
    
    # Database
    'DATABASE_PATH', 'DATABASE_BACKUP_ENABLED', 'DATABASE_BACKUP_INTERVAL_HOURS',
    
    # Logging
    'LOG_LEVEL', 'LOG_FILE', 'LOG_MAX_BYTES', 'LOG_BACKUP_COUNT',
    
    # Performance
    'USE_GPU', 'WORKER_THREADS',
    
    # Feature Flags
    'ENABLE_CURSOR_DETECTION', 'ENABLE_AUDIO_ANALYSIS', 
    'ENABLE_VISION_ANALYSIS', 'ENABLE_AUTO_EDITS',
    
    # Development
    'DEBUG_MODE', 'SAVE_INTERMEDIATE_FILES',
    
    # Functions
    'validate_settings'
]
