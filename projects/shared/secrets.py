#!/usr/bin/env python3
"""
Unified Secrets Management for OMOP Cohort Workflow

Works across multiple environments:
- Local development (.env file)
- Cloud Run (Google Cloud Secret Manager)
- Replit (environment variables)
- Any cloud platform with env vars

Usage:
    from shared.secrets import get_secret, check_credentials
    
    openai_key = get_secret("OPENAI_API_KEY")
    check_credentials()  # Verify all required secrets
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class SecretConfig:
    """Configuration for a secret."""
    name: str
    required: bool = True
    description: str = ""
    env_names: List[str] = None  # Alternative environment variable names
    
    def __post_init__(self):
        if self.env_names is None:
            self.env_names = [self.name]


# Define all secrets used by the application
SECRETS = [
    SecretConfig(
        name="OPENAI_API_KEY",
        required=True,
        description="OpenAI API key for GPT models",
        env_names=["OPENAI_API_KEY", "OPENAI_KEY"]
    ),
    SecretConfig(
        name="GOOGLE_APPLICATION_CREDENTIALS",
        required=False,
        description="Path to Google Cloud service account key (for BigQuery)",
        env_names=["GOOGLE_APPLICATION_CREDENTIALS", "GCP_CREDENTIALS_PATH"]
    ),
    SecretConfig(
        name="GOOGLE_CLOUD_PROJECT",
        required=False,
        description="Google Cloud project ID (for BigQuery)",
        env_names=["GOOGLE_CLOUD_PROJECT", "GCP_PROJECT_ID", "GCLOUD_PROJECT"]
    ),
]


def _load_dotenv() -> bool:
    """
    Load environment variables from .env file if it exists.
    
    Returns:
        True if .env was loaded, False otherwise
    """
    try:
        from dotenv import load_dotenv
        
        # Try multiple locations for .env
        locations = [
            Path.cwd() / ".env",  # Current directory
            Path(__file__).parent.parent.parent / ".env",  # Project root
            Path.home() / ".env",  # User home
        ]
        
        for env_path in locations:
            if env_path.exists():
                load_dotenv(env_path, override=True)
                return True
        
        return False
    except ImportError:
        # python-dotenv not installed, skip
        return False


def _check_cloud_run() -> bool:
    """Check if running in Google Cloud Run."""
    return os.getenv("K_SERVICE") is not None


def _check_replit() -> bool:
    """Check if running in Replit."""
    return os.getenv("REPL_ID") is not None or os.getenv("REPLIT_DB_URL") is not None


def _get_environment() -> str:
    """
    Detect current runtime environment.
    
    Returns:
        Environment name: "cloud_run", "replit", "local"
    """
    if _check_cloud_run():
        return "cloud_run"
    elif _check_replit():
        return "replit"
    else:
        return "local"


def _try_google_secret_manager(secret_name: str) -> Optional[str]:
    """
    Try to get secret from Google Cloud Secret Manager.
    
    This is used in Cloud Run or when explicitly configured.
    
    Args:
        secret_name: Name of the secret
        
    Returns:
        Secret value or None if not available
    """
    try:
        from google.cloud import secretmanager
        
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        
        if not project_id:
            return None
        
        # Build the resource name
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        
        # Access the secret
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
        
    except Exception:
        # Secret Manager not available or secret doesn't exist
        return None


def get_secret(secret_name: str, required: bool = True) -> Optional[str]:
    """
    Get a secret from the best available source.
    
    Priority order:
    1. Environment variable (works everywhere)
    2. Google Cloud Secret Manager (Cloud Run)
    3. .env file (local development)
    
    Args:
        secret_name: Name of the secret (e.g., "OPENAI_API_KEY")
        required: If True, raise error if secret not found
        
    Returns:
        Secret value or None if not found and not required
        
    Raises:
        ValueError: If secret is required but not found
    """
    # Load .env if in local environment
    env = _get_environment()
    if env == "local":
        _load_dotenv()
    
    # Find the secret config
    secret_config = next((s for s in SECRETS if s.name == secret_name), None)
    env_names = secret_config.env_names if secret_config else [secret_name]
    
    # Try environment variables (all alternative names)
    for env_name in env_names:
        value = os.getenv(env_name)
        if value:
            return value
    
    # Try Google Cloud Secret Manager (for Cloud Run)
    if env == "cloud_run":
        value = _try_google_secret_manager(secret_name)
        if value:
            return value
    
    # Not found
    if required:
        raise ValueError(
            f"Required secret '{secret_name}' not found. "
            f"Environment: {env}. "
            f"Tried: {', '.join(env_names)}"
        )
    
    return None


def check_credentials(verbose: bool = True) -> Dict[str, bool]:
    """
    Check if all required credentials are available.
    
    Args:
        verbose: If True, print status messages
        
    Returns:
        Dictionary mapping secret names to availability status
    """
    env = _get_environment()
    
    if verbose:
        print(f"🔐 Checking credentials (environment: {env})")
        print()
    
    status = {}
    all_required_found = True
    
    for secret in SECRETS:
        try:
            value = get_secret(secret.name, required=False)
            available = value is not None
            status[secret.name] = available
            
            if verbose:
                if available:
                    # Show partial value for confirmation
                    masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
                    icon = "✅" if secret.required else "✓"
                    print(f"{icon} {secret.name}: {masked}")
                else:
                    if secret.required:
                        icon = "❌"
                        all_required_found = False
                    else:
                        icon = "ℹ️"
                    print(f"{icon} {secret.name}: Not found")
                    if secret.description:
                        print(f"   ({secret.description})")
        except Exception as e:
            status[secret.name] = False
            if verbose:
                print(f"❌ {secret.name}: Error - {e}")
            if secret.required:
                all_required_found = False
    
    if verbose:
        print()
        if all_required_found:
            print("✅ All required credentials available!")
        else:
            print("⚠️  Some required credentials are missing")
            print()
            print("Setup instructions:")
            _print_setup_instructions(env)
    
    return status


def _print_setup_instructions(env: str):
    """Print environment-specific setup instructions."""
    print()
    
    if env == "local":
        print("📝 Local Development Setup:")
        print()
        print("1. Create a .env file in the project root:")
        print()
        print("   OPENAI_API_KEY=sk-...")
        print("   GOOGLE_CLOUD_PROJECT=your-project-id")
        print()
        print("2. For BigQuery, authenticate with:")
        print("   gcloud auth application-default login")
        print()
        
    elif env == "cloud_run":
        print("☁️  Cloud Run Setup:")
        print()
        print("1. Add secrets to Google Cloud Secret Manager:")
        print()
        print("   echo 'sk-...' | gcloud secrets create OPENAI_API_KEY --data-file=-")
        print()
        print("2. Grant Cloud Run access to secrets:")
        print()
        print("   gcloud run services update SERVICE_NAME \\")
        print("     --update-secrets=OPENAI_API_KEY=OPENAI_API_KEY:latest")
        print()
        print("3. Set environment variables:")
        print()
        print("   gcloud run services update SERVICE_NAME \\")
        print("     --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id")
        print()
        
    elif env == "replit":
        print("🔄 Replit Setup:")
        print()
        print("1. Go to 'Secrets' tab in Replit")
        print()
        print("2. Add secrets:")
        print("   - Key: OPENAI_API_KEY")
        print("     Value: sk-...")
        print()
        print("   - Key: GOOGLE_CLOUD_PROJECT")
        print("     Value: your-project-id")
        print()
        print("3. For BigQuery, add service account JSON:")
        print("   - Key: GOOGLE_APPLICATION_CREDENTIALS")
        print("     Value: /home/runner/service-account.json")
        print("   - Then upload the JSON file to Replit")
        print()


def setup_bigquery_auth() -> bool:
    """
    Set up BigQuery authentication.
    
    Returns:
        True if authentication is available, False otherwise
    """
    env = _get_environment()
    
    # Check if we have credentials path
    creds_path = get_secret("GOOGLE_APPLICATION_CREDENTIALS", required=False)
    
    if creds_path and Path(creds_path).exists():
        # Credentials file exists, set environment variable
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        return True
    
    # In Cloud Run, use default service account
    if env == "cloud_run":
        # Cloud Run automatically provides credentials
        return True
    
    # Try application default credentials
    try:
        from google.auth import default
        credentials, project = default()
        return True
    except Exception:
        return False


def check_openai_available() -> bool:
    """
    Check if OpenAI API key is available.
    
    Returns:
        True if OpenAI can be used
    """
    try:
        api_key = get_secret("OPENAI_API_KEY", required=False)
        return api_key is not None and len(api_key) > 0
    except Exception:
        return False


def check_bigquery_available() -> bool:
    """
    Check if BigQuery access is available.
    
    Returns:
        True if BigQuery can be used
    """
    return setup_bigquery_auth()


def get_runtime_info() -> Dict[str, any]:
    """
    Get information about the current runtime environment.
    
    Returns:
        Dictionary with runtime information
    """
    env = _get_environment()
    
    return {
        "environment": env,
        "openai_available": check_openai_available(),
        "bigquery_available": check_bigquery_available(),
        "google_project": get_secret("GOOGLE_CLOUD_PROJECT", required=False),
        "secrets_loaded": {
            "env_file": env == "local" and _load_dotenv(),
            "cloud_secrets": env == "cloud_run",
        }
    }


def main():
    """CLI to check credentials."""
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║         OMOP Cohort Workflow - Credentials Check                ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()
    
    # Check all credentials
    status = check_credentials(verbose=True)
    
    # Show runtime info
    print()
    print("━" * 70)
    print("Runtime Information:")
    print("━" * 70)
    info = get_runtime_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()
    
    # Exit with error if required credentials missing
    required_missing = any(
        not status.get(s.name, False) 
        for s in SECRETS 
        if s.required
    )
    
    if required_missing:
        print("❌ Setup incomplete - missing required credentials")
        sys.exit(1)
    else:
        print("✅ All systems ready!")
        sys.exit(0)


if __name__ == "__main__":
    main()
