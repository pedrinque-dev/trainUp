"""users.token_version: revogação de JWT (logout / troca de senha)

Revision ID: 0002
Revises: 0001

Idempotente: em bancos novos o baseline (create_all) já cria a coluna a partir do modelo atual.
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _has_column() -> bool:
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("users")}
    return "token_version" in cols


def upgrade() -> None:
    if _has_column():
        return
    with op.batch_alter_table("users") as b:
        b.add_column(sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    if _has_column():
        with op.batch_alter_table("users") as b:
            b.drop_column("token_version")
