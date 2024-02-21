# mypy: check_untyped_defs = False
from typing import List, Dict, Optional, Tuple, Any
from dacite import from_dict
from googleapiclient import discovery
from googleapiclient.errors import BatchError, HttpError
from googleapiclient.http import BatchHttpRequest
from httplib2 import HttpLib2Error
from google.auth.exceptions import DefaultCredentialsError

import threading
import os

from image2structure.filter.file_filters.file_filter import FileFilter, FileFilterError
from image2structure.filter.file_filters.repo_filter import list_files_in_dir
from image2structure.filter.file_filters.perspectiveapi.constants import (
    PerspectiveAPIRequest,
    PerspectiveAPIRequestResult,
    ToxicityAttributes,
)


class ToxicityFilter(FileFilter):
    """
    Perspective API predicts the perceived impact a comment may have on a conversation by evaluating that comment
    across a range of emotional concepts, called attributes. When you send a request to the API, you’ll request the
    specific attributes you want to receive scores for.

    The API is hosted on Google Cloud Platform.

    Source: https://developers.perspectiveapi.com/s/docs
    """

    # Maximum allowed text length by Perspective API
    MAX_TEXT_LENGTH: int = 20_400

    @staticmethod
    def create_request_body(
        text: str, attributes: List[str], languages: List[str]
    ) -> Dict:
        """Create an API request for a given text."""
        return {
            "comment": {"text": text},
            "requestedAttributes": {attribute: {} for attribute in attributes},
            "languages": languages,
            "spanAnnotations": True,
        }

    @staticmethod
    def extract_toxicity_attributes(response: Dict) -> ToxicityAttributes:
        """Given a response from PerspectiveAPI, return `ToxicityScores`."""
        all_scores = {
            f"{attribute.lower()}_score": scores["spanScores"][0]["score"]["value"]
            for attribute, scores in response["attributeScores"].items()
        }
        return from_dict(data_class=ToxicityAttributes, data=all_scores)

    def __init__(
        self,
        api_key: str,
        toxicity_threshold: float,
        sexually_explicit_threshold: float,
    ):
        super().__init__(name="ToxicityFilter")
        # API key obtained from GCP that works with PerspectiveAPI
        self.api_key = api_key
        self.toxicity_threshold = toxicity_threshold
        self.sexually_explicit_threshold = sexually_explicit_threshold

        # httplib2 is not thread-safe. Acquire this lock when sending requests to PerspectiveAPI
        self._client_lock: threading.Lock = threading.Lock()

        # Google Perspective API client.
        # The _client_lock must be held when creating or using the client.
        self._client: Optional[discovery.Resource] = None

    def _create_client(self) -> discovery.Resource:
        """Initialize the client."""
        if not self.api_key:
            raise FileFilterError("Perspective API key was not provided.")
        try:
            return discovery.build(
                "commentanalyzer",
                "v1alpha1",
                developerKey=self.api_key,
                discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
                static_discovery=False,
            )
        except DefaultCredentialsError as e:
            raise FileFilterError(
                f"Credentials error when creating Perspective API client: {e}"
            ) from e

    def get_toxicity_scores(
        self, request: PerspectiveAPIRequest
    ) -> PerspectiveAPIRequestResult:
        """
        Batch several requests into a single API request and get the toxicity attributes and scores.
        For more information, see https://googleapis.github.io/google-api-python-client/docs/batch.html.
        """

        with self._client_lock:
            if not self._client:
                self._client = self._create_client()

        try:
            text_to_response: Dict[str, Dict] = dict()

            def callback(request_id: str, response: Dict, error: HttpError):
                if error:
                    raise error
                text_to_response[request_id] = response

            # Create a batch request. We will add a request to the batch request for each text string
            batch_request: BatchHttpRequest = self._client.new_batch_http_request()

            # Add individual request to the batch request. Deduplicate since we use the text as request keys.
            for text in set(request.text_batch):
                batch_request.add(
                    request=self._client.comments().analyze(
                        body=ToxicityFilter.create_request_body(
                            text[: ToxicityFilter.MAX_TEXT_LENGTH],
                            request.attributes,
                            request.languages,
                        )
                    ),
                    request_id=text,
                    callback=callback,
                )

            with self._client_lock:
                batch_request.execute()
            batch_response = text_to_response

        except (BatchError, HttpLib2Error, HttpError) as e:
            return PerspectiveAPIRequestResult(
                success=False,
                error=f"Error was thrown when making a request to Perspective API: {e}",
            )

        return PerspectiveAPIRequestResult(
            success=True,
            text_to_toxicity_attributes={
                text: ToxicityFilter.extract_toxicity_attributes(response)
                for text, response in batch_response.items()
            },
        )

    def filter(self, file_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Filter a repository based on the parameters

        Args:
            file_path (str): The path to the repository

        Returns:
            bool: Whether the repository passes the filter
            Dict[str, Dict[str, int]]: The analysis of the repository
        """
        # Check if file_path is the path to a directory or file
        list_files: List[str] = []
        if os.path.isdir(file_path):
            list_files = list_files_in_dir(file_path)
        else:
            list_files = [file_path]

        # Read the content of the files
        text_to_file: Dict[str, str] = {}
        for file in list_files:
            try:
                with open(os.path.join(file_path, file), "r") as f:
                    text_to_file[f.read()] = file
            except UnicodeDecodeError:
                pass

        # Create a request to the Perspective API
        request = PerspectiveAPIRequest(text_batch=text_to_file.keys())
        result: PerspectiveAPIRequestResult = self.get_toxicity_scores(request)

        # If the request was not successful, return False as we could not filter the files
        if not result.success:
            return False, {
                "error": result.error,
                "text_to_toxicity_attributes": {
                    text_to_file[text]: attributes.to_dict()
                    for text, attributes in result.text_to_toxicity_attributes.items()
                },
            }

        # If the request was successful, check the thresholds
        is_toxic: bool = False
        reason: Optional[str] = None
        for _, attributes in result.text_to_toxicity_attributes.items():
            if attributes.toxicity_score > self.toxicity_threshold:
                reason = "Toxicity score is above the threshold"
                is_toxic = True
                break
            if attributes.sexually_explicit_score > self.sexually_explicit_threshold:
                reason = "Sexually explicit score is above the threshold"
                is_toxic = True
                break
        return not is_toxic, {
            "text_to_toxicity_attributes": {
                text: attributes.to_dict()
                for text, attributes in result.text_to_toxicity_attributes.items()
            },
            "reason": reason,
        }
