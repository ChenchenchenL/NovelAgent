from novelagent.integrations.model_gateway import ModelConfig, ModelGateway


def test_gateway_records_project_scoped_context():
    gateway = ModelGateway(ModelConfig(endpoint="https://api.example.com/v1"))
    manifest = gateway.context_manifest(project_id=42, source_ids=["doc_1", "doc_2"])
    assert manifest["project_id"] == 42
    assert manifest["scope"] == "project"
    assert manifest["policy"] == "project_default_current_project_only"
