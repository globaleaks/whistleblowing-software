# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase

from globaleaks.models import Model
from globaleaks.models.properties import *


class FieldOption_v_47(Model):
    __tablename__ = 'fieldoption'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    field_id = Column(UnicodeText(36), nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    label = Column(JSON, nullable=False)
    score_points = Column(Integer, default=0, nullable=False)
    score_type = Column(Integer, default=0, nullable=False)
    trigger_receiver = Column(JSON, default=list, nullable=True)


class MigrationScript(MigrationBase):
    pass
