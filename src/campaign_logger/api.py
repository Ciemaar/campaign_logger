import requests
from typing import List, Optional, Union, Dict
from .models import FullGeneratorModel, GeneratorModelContainer

class GeneratorClient:
    def __init__(self, base_url: str = "https://generator.campaign-logger.com", token: str = None, client_id: str = None, client_secret: str = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        if client_id and client_secret:
            self.session.headers.update({
                "api-client": client_id,
                "api-secret": client_secret
            })

        self.session.headers.update({"Content-Type": "application/json"})

    def list_generators(self) -> List[FullGeneratorModel]:
        """Gets all generators of the current user."""
        url = f"{self.base_url}/api2/generators"
        response = self.session.get(url)
        response.raise_for_status()
        # Assuming the API returns a list of FullGeneratorModel
        return [FullGeneratorModel(**g) for g in response.json()]

    def get_generator(self, generator_id: str) -> FullGeneratorModel:
        """Gets the generator identified by {id}."""
        url = f"{self.base_url}/api2/generators/{generator_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return FullGeneratorModel(**response.json())

    def create_generator(self, model: FullGeneratorModel) -> FullGeneratorModel:
        """Stores the generator provided in the body of the request."""
        url = f"{self.base_url}/api2/generators"
        response = self.session.post(url, json=model.model_dump(exclude_unset=True))
        response.raise_for_status()
        return FullGeneratorModel(**response.json())

    def update_generator(self, generator_id: str, model: FullGeneratorModel) -> FullGeneratorModel:
        """Updates the generator identified by {id} overwriting it with the request body."""
        url = f"{self.base_url}/api2/generators/{generator_id}"
        response = self.session.put(url, json=model.model_dump(exclude_unset=True))
        response.raise_for_status()
        return FullGeneratorModel(**response.json())

    def delete_generator(self, generator_id: str) -> None:
        """Deletes the generator identified by {id}."""
        url = f"{self.base_url}/api2/generators/{generator_id}"
        response = self.session.delete(url)
        response.raise_for_status()

    def validate_generator(self, model: FullGeneratorModel) -> None:
        """Executes validate on the generator provided in the body."""
        url = f"{self.base_url}/api2/generators/validate"
        response = self.session.post(url, json=model.model_dump(exclude_unset=True))
        response.raise_for_status()

    def generate_random(self, model: FullGeneratorModel) -> Dict:
        """Executes generate on the generator provided in the body."""
        url = f"{self.base_url}/api2/generators/generate"
        response = self.session.post(url, json=model.model_dump(exclude_unset=True))
        response.raise_for_status()
        return response.json()

    def execute_operation(self, generator_id: str, operation: str) -> Dict:
        """Executes {operation} on the generator identified by {id}."""
        if operation not in ["validate", "generate"]:
            raise ValueError("Operation must be 'validate' or 'generate'")
        url = f"{self.base_url}/api2/generators/{generator_id}/{operation}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json() if response.content else {}

    def get_execute_tokens(self, generator_id: str) -> List[str]:
        """Gets all execute-tokens for the generator identified by {id}."""
        url = f"{self.base_url}/api2/generators/{generator_id}/execute-tokens"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def create_execute_token(self, generator_id: str) -> str:
        """Creates a new execute-token for the generator identified by {id}."""
        url = f"{self.base_url}/api2/generators/{generator_id}/execute-tokens"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()

    def delete_execute_token(self, generator_id: str, token: str) -> None:
        """Deletes the execute-token {token} for the generator identified by {id}."""
        url = f"{self.base_url}/api2/generators/{generator_id}/execute-tokens/{token}"
        response = self.session.delete(url)
        response.raise_for_status()
