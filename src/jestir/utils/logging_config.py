"""Logging configuration for Jestir CLI."""

import logging
import os
from pathlib import Path


def setup_logging(verbose: bool = False, log_to_disk: bool | None = None) -> None:
    """
    Set up logging configuration for Jestir.

    Args:
        verbose: Enable verbose console logging (DEBUG level)
        log_to_disk: Enable disk logging. If None, reads from JESTIR_LOG_TO_DISK env var
    """
    # Determine log level
    log_level = logging.DEBUG if verbose else logging.INFO

    # Determine if we should log to disk
    if log_to_disk is None:
        log_to_disk = os.getenv("JESTIR_LOG_TO_DISK", "false").lower() == "true"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Disk handler (if enabled)
    if log_to_disk:
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Create file handler
        log_file = logs_dir / "jestir.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always DEBUG for file logging
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Log the logging setup
        logger = logging.getLogger(__name__)
        logger.info(f"Disk logging enabled. Log file: {log_file}")

    # Set specific loggers to appropriate levels
    _configure_logger_levels(verbose)


def _configure_logger_levels(verbose: bool) -> None:
    """Configure specific logger levels for different components."""
    # Set external library loggers to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Set our loggers to appropriate levels
    if verbose:
        logging.getLogger("jestir").setLevel(logging.DEBUG)
    else:
        logging.getLogger("jestir").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"jestir.{name}")


def log_command_start(command_name: str, args: dict, logger: logging.Logger) -> None:
    """
    Log the start of a command execution.

    Args:
        command_name: Name of the command being executed
        args: Command arguments (excluding sensitive data)
        logger: Logger instance to use
    """
    # Filter out sensitive arguments
    safe_args = {
        k: v
        for k, v in args.items()
        if "key" not in k.lower() and "password" not in k.lower()
    }
    logger.debug(f"Starting command '{command_name}' with args: {safe_args}")


def log_command_end(command_name: str, success: bool, logger: logging.Logger) -> None:
    """
    Log the end of a command execution.

    Args:
        command_name: Name of the command being executed
        success: Whether the command completed successfully
        logger: Logger instance to use
    """
    status = "completed successfully" if success else "failed"
    logger.debug(f"Command '{command_name}' {status}")


def log_api_call(service: str, endpoint: str, logger: logging.Logger, **kwargs) -> None:
    """
    Log an API call.

    Args:
        service: Name of the service (e.g., "OpenAI", "LightRAG")
        endpoint: API endpoint being called
        logger: Logger instance to use
        **kwargs: Additional context to log
    """
    context = " ".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])
    logger.debug(f"API call to {service} {endpoint} - {context}")


def log_file_operation(
    operation: str,
    file_path: str,
    logger: logging.Logger,
    **kwargs,
) -> None:
    """
    Log a file operation.

    Args:
        operation: Type of operation (read, write, delete, etc.)
        file_path: Path to the file
        logger: Logger instance to use
        **kwargs: Additional context to log
    """
    context = " ".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])
    logger.debug(f"File {operation}: {file_path} - {context}")
