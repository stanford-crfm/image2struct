from dataclasses import dataclass, field
from typing import List, Optional, Dict


DEFAULT_ATTRIBUTES = [
    "TOXICITY",
    "SEVERE_TOXICITY",
    "IDENTITY_ATTACK",
    "INSULT",
    "PROFANITY",
    "THREAT",
    "SEXUALLY_EXPLICIT",
    "FLIRTATION",
]


@dataclass(frozen=True)
class PerspectiveAPIRequest:
    """
    A `PerspectiveAPIRequest` specifies how to calculate toxicity scores using PerspectiveAPI for a batch of text.
    Note: not all attributes are supported across all the different languages.

    For more information on the languages and attributes, see the following documentation:
    https://developers.perspectiveapi.com/s/about-the-api-attributes-and-languages
    """

    # Batch of text to calculate toxicity scores.
    text_batch: List[str] = field(default_factory=list)

    # Attributes to calculate scores for.
    attributes: List[str] = field(default_factory=lambda: DEFAULT_ATTRIBUTES)

    # Languages to use.
    languages: List[str] = field(default_factory=lambda: ["en"])


@dataclass(frozen=True)
class ToxicityAttributes:
    """
    Toxicity attributes and scores calculated by PerspectiveAPI. All scores are a value from 0 to 1.
    For a list of supported attributes and their description, see the following documentation:
    https://developers.perspectiveapi.com/s/about-the-api-attributes-and-languages
    """

    # Attribute: TOXICITY
    toxicity_score: Optional[float] = None

    # Attribute: SEVERE_TOXICITY
    severe_toxicity_score: Optional[float] = None

    # Attribute: IDENTITY_ATTACK
    identity_attack_score: Optional[float] = None

    # Attribute: INSULT
    insult_score: Optional[float] = None

    # Attribute: PROFANITY
    profanity_score: Optional[float] = None

    # Attribute: THREAT
    threat_score: Optional[float] = None

    # Attribute: SEXUALLY_EXPLICIT
    sexually_explicit_score: Optional[float] = None

    # Attribute: FLIRTATION
    flirtation_score: Optional[float] = None

    # Make JSON serializable
    def to_dict(self) -> Dict[str, Optional[float]]:
        return {
            "toxicity_score": self.toxicity_score,
            "severe_toxicity_score": self.severe_toxicity_score,
            "identity_attack_score": self.identity_attack_score,
            "insult_score": self.insult_score,
            "profanity_score": self.profanity_score,
            "threat_score": self.threat_score,
            "sexually_explicit_score": self.sexually_explicit_score,
            "flirtation_score": self.flirtation_score,
        }


@dataclass(frozen=True)
class PerspectiveAPIRequestResult:
    """Result after sending a `PerspectiveAPIRequest`."""

    # Whether the request was successful
    success: bool

    # Batch of text to calculate toxicity scores.
    text_to_toxicity_attributes: Dict[str, ToxicityAttributes] = field(
        default_factory=dict
    )

    # If `success` is false, what was the error?
    error: Optional[str] = None
