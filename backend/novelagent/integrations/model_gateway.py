from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

import httpx

logger = logging.getLogger(__name__)
SERVICE_NAME = "novelagent_model_gateway"


class KeyringManager:
    """Manages API keys with system keyring and safe in-memory/session fallback."""
    _memory_fallback: dict[str, str] = {}

    @classmethod
    def save_key(cls, username: str, key: str) -> None:
        try:
            import keyring
            keyring.set_password(SERVICE_NAME, username, key)
        except Exception as exc:
            logger.warning("Failed to store API key in system keyring, using memory fallback: %s", exc)
            cls._memory_fallback[f"{SERVICE_NAME}:{username}"] = key

    @classmethod
    def load_key(cls, username: str) -> str | None:
        try:
            import keyring
            val = keyring.get_password(SERVICE_NAME, username)
            if val is not None:
                return val
        except Exception:
            pass
        return cls._memory_fallback.get(f"{SERVICE_NAME}:{username}")

    @classmethod
    def delete_key(cls, username: str) -> None:
        try:
            import keyring
            keyring.delete_password(SERVICE_NAME, username)
        except Exception:
            pass
        cls._memory_fallback.pop(f"{SERVICE_NAME}:{username}", None)


@dataclass(frozen=True)
class ModelConfig:
    endpoint: str = ""
    models: dict[str, str] = field(default_factory=lambda: {
        "T1": "small-extraction",
        "T2": "medium-planning",
        "T3": "frontier-writing",
    })
    timeout_seconds: int = 60
    max_retries: int = 3
    retry_backoff_multiplier: float = 2.0
    project_scope_default: bool = True


class ModelRouter:
    """Routes tasks to model tiers and handles degradation."""
    TASK_TIER_MAPPING: dict[str, str] = {
        "rules_eval": "T0",
        "diff_calc": "T0",
        "conservation_check": "T0",
        "extraction_entity": "T1",
        "extraction_claim": "T1",
        "scene_summary": "T1",
        "cliche_scan": "T1",
        "beat_plan": "T2",
        "continuity_check": "T2",
        "quality_check": "T2",
        "paragraph_generation": "T3",
        "full_scene_generation": "T3",
        "global_analysis": "T3",
    }

    def __init__(self, config: ModelConfig):
        self.config = config

    def route(self, task_type: str, preferred_tier: str | None = None) -> tuple[str, str]:
        tier = preferred_tier or self.TASK_TIER_MAPPING.get(task_type, "T2")
        model = self.config.models.get(tier, self.config.models.get("T3", "mock-model"))
        return tier, model

    @staticmethod
    def get_degraded_tier(current_tier: str) -> str | None:
        if current_tier == "T3":
            return "T2"
        if current_tier == "T2":
            return "T1"
        return None  # T0 and T1 cannot degrade further


class ModelGateway:
    """Gateway for OpenAI-compatible LLM endpoints and test simulations."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.router = ModelRouter(config)

    def context_manifest(self, project_id: int, source_ids: list[str], scope: str = "project", token_budget: int = 8192) -> dict:
        return {
            "project_id": project_id,
            "scope": scope,
            "source_ids": source_ids,
            "policy": "project_default_current_project_only",
            "token_budget": token_budget,
            "allowed_domains": ["author-confirmed"],
            "excluded_modes": ["DREAMED", "HYPOTHETICAL"],
        }

    async def stream_chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        api_key: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        endpoint = (self.config.endpoint or "").rstrip("/")
        if not endpoint or endpoint.startswith("mock") or endpoint.startswith("test"):
            # Mock Streaming for local tests and offline mode
            sample_chunks = [
                "林舟按住剑柄，",
                "缓步推开客栈后门，",
                "寒风夹着雪沫扑面而来。",
                "长街寂静，唯有远处传来三两声更鼓。",
            ]
            total_text = ""
            for i, chunk in enumerate(sample_chunks):
                await asyncio.sleep(0.02)
                total_text += chunk
                yield {
                    "type": "chunk",
                    "delta": chunk,
                    "index": i,
                    "partial_content": total_text,
                }
            yield {
                "type": "usage",
                "usage": {
                    "prompt_tokens": len(str(messages)) // 4,
                    "completion_tokens": len(total_text) // 2,
                    "total_tokens": len(str(messages)) // 4 + len(total_text) // 2,
                },
                "final_content": total_text,
            }
            return

        # Real OpenAI-compatible Streaming over HTTP
        url = f"{endpoint}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key or ''}",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        accumulated = ""
        index = 0
        prompt_tokens = len(str(messages)) // 4
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise RuntimeError(f"HTTP {response.status_code}: {error_text.decode('utf-8', errors='replace')}")

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            delta_content = choices[0].get("delta", {}).get("content", "")
                            if delta_content:
                                accumulated += delta_content
                                yield {
                                    "type": "chunk",
                                    "delta": delta_content,
                                    "index": index,
                                    "partial_content": accumulated,
                                }
                                index += 1
                        if data.get("usage"):
                            usage = data["usage"]
                    except json.JSONDecodeError:
                        continue

        yield {
            "type": "usage",
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": len(accumulated) // 2,
                "total_tokens": prompt_tokens + len(accumulated) // 2,
            },
            "final_content": accumulated,
        }

    async def test_connection(self, api_key: str | None = None) -> dict[str, Any]:
        endpoint = (self.config.endpoint or "").rstrip("/")
        if not endpoint or endpoint.startswith("mock") or endpoint.startswith("test"):
            return {
                "status": "ok",
                "endpoint": endpoint or "mock://local",
                "models": list(self.config.models.values()),
            }

        url = f"{endpoint}/models"
        headers = {"Authorization": f"Bearer {api_key or ''}"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    model_list = [m.get("id") for m in data.get("data", []) if isinstance(m, dict)]
                    return {"status": "ok", "endpoint": endpoint, "models": model_list or list(self.config.models.values())}
                return {"status": "error", "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}
