"""System initialization script."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logging, get_logger
from src.storage.chroma_client import ChromaClient

logger = get_logger(__name__)


def init_system():
    """Initialize the system."""
    print("Initializing Agentic RAG Document Generator...")

    # Setup logging
    print("Setting up logging...")
    setup_logging()
    logger.info("logging_initialized")

    # Initialize Chroma database
    print("Initializing Chroma database...")
    try:
        chroma = ChromaClient()
        stats = chroma.get_stats()
        logger.info("chroma_initialized", stats=stats)
        print(f"[OK] Chroma initialized: {stats['document_count']} documents")
    except Exception as e:
        logger.error("chroma_initialization_failed", error=str(e))
        print(f"[ERROR] Chroma initialization failed: {e}")
        return False

    # Create necessary directories
    print("Creating directories...")
    directories = [
        "data/documents",
        "data/chroma_db",
        "logs"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {directory}")

    print("\n[SUCCESS] System initialized successfully!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and configure your API keys")
    print("2. Run: streamlit run ui/app.py")
    print("3. Visit: http://localhost:8501")

    return True


if __name__ == "__main__":
    success = init_system()
    sys.exit(0 if success else 1)
