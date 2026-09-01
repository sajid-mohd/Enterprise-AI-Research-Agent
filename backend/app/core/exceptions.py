"""Domain exceptions for Research Agent."""


class ResearchAgentError(Exception):
    """Base exception."""


class ResearchError(ResearchAgentError):
    """Raised when the research pipeline fails."""


class SearchError(ResearchAgentError):
    """Raised when all search providers fail."""


class AIError(ResearchAgentError):
    """Raised when the LLM call fails after retries."""


class NotFoundError(ResearchAgentError):
    """Raised when a resource is not found in the DB."""


class ValidationError(ResearchAgentError):
    """Raised when input validation fails."""