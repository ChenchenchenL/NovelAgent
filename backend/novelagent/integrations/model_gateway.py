from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelConfig:
    endpoint: str
    models: dict[str, str] = field(default_factory=lambda: {
        "T1": "small-extraction",
        "T2": "medium-planning",
        "T3": "frontier-writing",
    })
    project_scope_default: bool = True


class ModelGateway:
    """OpenAI-compatible gateway boundary; transport adapters can be added later."""

    def __init__(self, config: ModelConfig):
        self.config = config

    def model_for(self, tier: str) -> str:
        if tier not in self.config.models:
            raise ValueError(f"unsupported model tier: {tier}")
        return self.config.models[tier]

    def context_manifest(self, project_id: int, source_ids: list[str], scope: str = "project") -> dict:
        return {
            "project_id": project_id,
            "scope": scope,
            "source_ids": source_ids,
            "policy": "project_default_current_project_only",
        }

    @staticmethod
    def save_key(service: str, username: str, secret: str) -> None:
        import keyring

        keyring.set_password(service, username, secret)

    @staticmethod
    def load_key(service: str, username: str) -> str | None:
        import keyring

        return keyring.get_password(service, username)
