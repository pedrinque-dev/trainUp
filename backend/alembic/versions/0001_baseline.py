"""baseline: cria o esquema atual do TrainUp

Revision ID: 0001
Revises:

Esta revisão cria todas as tabelas a partir do modelo vigente (checkfirst). Mudanças futuras
no modelo devem virar NOVAS revisões (`alembic revision --autogenerate -m "..."`).
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    import app.models  # noqa: F401
    from app.database import Base

    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    import app.models  # noqa: F401
    from app.database import Base

    Base.metadata.drop_all(bind=op.get_bind())
