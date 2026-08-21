"""Stage 6 character, item, identity and space continuity schema.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-21
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Characters & CharacterStates
    op.create_table(
        "characters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("aliases", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("background", sa.Text(), nullable=True),
        sa.Column("core_traits", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_characters_project_id", "characters", ["project_id"])

    op.create_table(
        "character_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("character_id", sa.Integer(), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("scene_id", sa.Integer(), sa.ForeignKey("scenes.id"), nullable=False),
        sa.Column("narrative_time", sa.String(64), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("physical_state", sa.String(255), nullable=True),
        sa.Column("goal", sa.String(255), nullable=True),
        sa.Column("faction", sa.String(255), nullable=True),
        sa.Column("emotion", sa.String(255), nullable=True),
        sa.Column("arc_stage", sa.String(64), nullable=True),
        sa.Column("confirmed", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index("ix_character_states_character_id", "character_states", ["character_id"])
    op.create_index("ix_character_states_scene_id", "character_states", ["scene_id"])

    # 2. RelationshipEvents & RelationshipStates
    op.create_table(
        "relationship_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("subject_character_id", sa.Integer(), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("object_character_id", sa.Integer(), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("relationship_type", sa.String(32), nullable=False),
        sa.Column("scene_id", sa.Integer(), sa.ForeignKey("scenes.id"), nullable=False),
        sa.Column("narrative_time", sa.String(64), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("confirmed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_relationship_events_project_id", "relationship_events", ["project_id"])
    op.create_index("ix_relationship_events_subject", "relationship_events", ["subject_character_id"])
    op.create_index("ix_relationship_events_object", "relationship_events", ["object_character_id"])

    op.create_table(
        "relationship_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("subject_character_id", sa.Integer(), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("object_character_id", sa.Integer(), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("relationship_type", sa.String(32), nullable=False),
        sa.Column("as_of_scene_id", sa.Integer(), sa.ForeignKey("scenes.id"), nullable=False),
        sa.Column("as_of_narrative_time", sa.String(64), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "subject_character_id", "object_character_id", name="uq_relationship_subject_object"),
    )
    op.create_index("ix_relationship_states_project_id", "relationship_states", ["project_id"])

    # 3. NarrativeSecrets & InformationGaps
    op.create_table(
        "narrative_secrets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("secret_name", sa.String(255), nullable=False),
        sa.Column("secret_content", sa.Text(), nullable=False),
        sa.Column("created_scene_id", sa.Integer(), sa.ForeignKey("scenes.id"), nullable=False),
        sa.Column("created_narrative_time", sa.String(64), nullable=True),
        sa.Column("known_by", sa.JSON(), server_default="[]", nullable=False),
    )
    op.create_index("ix_narrative_secrets_project_id", "narrative_secrets", ["project_id"])

    op.create_table(
        "information_gaps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("character_id", sa.Integer(), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("fact_description", sa.Text(), nullable=False),
        sa.Column("knows", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("last_updated_scene_id", sa.Integer(), sa.ForeignKey("scenes.id"), nullable=False),
    )
    op.create_index("ix_information_gaps_project_id", "information_gaps", ["project_id"])
    op.create_index("ix_information_gaps_character_id", "information_gaps", ["character_id"])

    # 4. IdentityHypotheses & IdentityRevealEvents
    op.create_table(
        "identity_hypotheses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shadow_entity_id", sa.Integer(), sa.ForeignKey("shadow_entities.id"), nullable=False),
        sa.Column("canonical_character_id", sa.Integer(), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("evidence", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("earliest_reveal_scene_id", sa.Integer(), sa.ForeignKey("scenes.id"), nullable=True),
        sa.Column("confirmed", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index("ix_identity_hypotheses_shadow", "identity_hypotheses", ["shadow_entity_id"])
    op.create_index("ix_identity_hypotheses_canonical", "identity_hypotheses", ["canonical_character_id"])

    op.create_table(
        "identity_reveal_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shadow_entity_id", sa.Integer(), sa.ForeignKey("shadow_entities.id"), nullable=False),
        sa.Column("canonical_character_id", sa.Integer(), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("reveal_scene_id", sa.Integer(), sa.ForeignKey("scenes.id"), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("reader_visibility", sa.String(32), server_default="FULL", nullable=False),
        sa.Column("character_knowledge", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_identity_reveal_shadow", "identity_reveal_events", ["shadow_entity_id"])
    op.create_index("ix_identity_reveal_canonical", "identity_reveal_events", ["canonical_character_id"])

    # 5. Locations, TravelProfiles, MovementEvents
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("parent_location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("coordinates", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_locations_project_id", "locations", ["project_id"])

    op.create_table(
        "travel_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("from_location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("to_location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("travel_mode", sa.String(32), nullable=False),
        sa.Column("min_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("distance_units", sa.Float(), nullable=True),
        sa.Column("special_rules", sa.Text(), nullable=True),
        sa.UniqueConstraint("project_id", "from_location_id", "to_location_id", "travel_mode", name="uq_travel_profile"),
    )
    op.create_index("ix_travel_profiles_project_id", "travel_profiles", ["project_id"])

    op.create_table(
        "movement_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("subject_type", sa.String(16), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("from_location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("to_location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("travel_mode", sa.String(32), nullable=False),
        sa.Column("departure_scene_id", sa.Integer(), sa.ForeignKey("scenes.id"), nullable=False),
        sa.Column("arrival_scene_id", sa.Integer(), sa.ForeignKey("scenes.id"), nullable=False),
        sa.Column("departure_time", sa.String(64), nullable=True),
        sa.Column("arrival_time", sa.String(64), nullable=True),
        sa.Column("actual_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("confirmed", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index("ix_movement_events_project_id", "movement_events", ["project_id"])
    op.create_index("ix_movement_events_subject", "movement_events", ["subject_type", "subject_id"])

    # 6. Alter items, item_events, shadow_entities
    with op.batch_alter_table("items") as batch_op:
        batch_op.add_column(sa.Column("current_location", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("derived_from_id", sa.Integer(), sa.ForeignKey("items.id", name="fk_items_derived_from_id"), nullable=True))

    with op.batch_alter_table("item_events") as batch_op:
        batch_op.add_column(sa.Column("from_location", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("to_location", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("narrative_time", sa.String(64), nullable=True))
        batch_op.add_column(sa.Column("evidence", sa.Text(), nullable=True))

    with op.batch_alter_table("shadow_entities") as batch_op:
        batch_op.add_column(sa.Column("canonical_character_id", sa.Integer(), sa.ForeignKey("characters.id", name="fk_shadow_canonical_character_id"), nullable=True))
        batch_op.add_column(sa.Column("revealed", sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("shadow_entities") as batch_op:
        batch_op.drop_column("revealed")
        batch_op.drop_column("canonical_character_id")

    with op.batch_alter_table("item_events") as batch_op:
        batch_op.drop_column("evidence")
        batch_op.drop_column("narrative_time")
        batch_op.drop_column("to_location")
        batch_op.drop_column("from_location")

    with op.batch_alter_table("items") as batch_op:
        batch_op.drop_column("derived_from_id")
        batch_op.drop_column("current_location")

    op.drop_table("movement_events")
    op.drop_table("travel_profiles")
    op.drop_table("locations")
    op.drop_table("identity_reveal_events")
    op.drop_table("identity_hypotheses")
    op.drop_table("information_gaps")
    op.drop_table("narrative_secrets")
    op.drop_table("relationship_states")
    op.drop_table("relationship_events")
    op.drop_table("character_states")
    op.drop_table("characters")
