# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.enums import EnumVisibility
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_never, datetime_now, datetime_null

from globaleaks.db.migrations.update import MigrationBase as MigrationScript


class ReceiverFile_v_66(Model):
    __tablename__ = 'whistleblowerfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    internaltip_id = Column(UnicodeText(36), nullable=False, index=True)
    name = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    access_date = Column(DateTime, default=datetime_null, nullable=False)
    description = Column(UnicodeText, default="", nullable=False)
    visibility = Column(Enum(EnumVisibility), default='public', nullable=False)
    new = Column(Boolean, default=True, nullable=False)


class Redaction_v_66(Model):
    __tablename__ = 'redaction'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    reference_id = Column(UnicodeText(36), nullable=False, index=True)
    internaltip_id = Column(UnicodeText(36), nullable=False, index=True)
    temporary_redaction = Column(JSON, default=dict, nullable=False)
    permanent_redaction = Column(JSON, default=dict, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)


class WhistleblowerFile_v_66(Model):
    __tablename__ = 'receiverfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    internalfile_id = Column(UnicodeText(36), nullable=False, index=True)
    receivertip_id = Column(UnicodeText(36), nullable=False, index=True)
    access_date = Column(DateTime, default=datetime_null, nullable=False)
    new = Column(Boolean, default=True, nullable=False)
