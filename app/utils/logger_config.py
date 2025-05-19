import logging
import sys

def get_request_logger(name: str = "recipe_app.request") -> logging.Logger:
    """
    Configures and returns a logger instance, typically for request-specific logging.
    """
    logger = logging.getLogger(name)
    
    # Prevent adding multiple handlers if this function is called multiple times for the same logger name
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)  # Set the default level for this logger

        # Create a console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG) # Log DEBUG and above to console

        # Create a formatter and set it for the handler
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        console_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(console_handler)
        
        # Optional: Prevent propagation to the root logger if you want this logger to be independent
        # logger.propagate = False

    return logger

# Example of a general application logger (can be defined here or elsewhere)
def get_app_logger(name: str = "recipe_app.general") -> logging.Logger:
    """
    Configures and returns a general application logger.
    """
    # This could have different handlers or levels, e.g., log to a file
    # For simplicity, using a similar setup as get_request_logger for now
    return get_request_logger(name)


if __name__ == '__main__':
    # Example usage:
    req_logger = get_request_logger()
    req_logger.debug("This is a debug message from request logger.")
    req_logger.info("This is an info message from request logger.")

    app_logger = get_app_logger()
    app_logger.error("This is an error message from app logger.")
