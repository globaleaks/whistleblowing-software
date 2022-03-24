from globaleaks.db.migrations.update import MigrationBase as MigrationScript

from globaleaks.models import *
from globaleaks.models.properties import *


class FieldAnswer_v_39(Model):
    __tablename__ = 'fieldanswer'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    internaltip_id = Column(UnicodeText(36), nullable=True)
    fieldanswergroup_id = Column(UnicodeText(36), nullable=True)
    is_leaf = Column(Boolean, default=True, nullable=False)
    key = Column(UnicodeText, default='', nullable=False)
    value = Column(UnicodeText, default='', nullable=False)


class FieldAnswerGroup_v_39(Model):
    __tablename__ = 'fieldanswergroup'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    number = Column(Integer, default=0)
    fieldanswer_id = Column(UnicodeText(36))
