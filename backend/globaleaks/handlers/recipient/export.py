# -*- coding: utf-8 -*-
#
# API handling export of submissions
import os
from io import BytesIO
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread

from globaleaks import models
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.public import db_get_submission_statuses
from globaleaks.handlers.recipient.rtip import db_update_submission_status, redact_report
from globaleaks.handlers.whistleblower.submission import decrypt_tip
from globaleaks.handlers.user import user_serialize_user
from globaleaks.models import serializers
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.utils.crypto import Base64Encoder, GCE
from globaleaks.utils.fs import directory_traversal_check
from globaleaks.utils.securetempfile import SecureTemporaryFile
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import datetime_now, datetime_null, msdos_encode
from globaleaks.utils.zipstream import ZipStream
import io

import pkgutil
if pkgutil.find_loader("fpdf") is not None:
    fpdf_installed = True
    from fpdf import FPDF
else:
    fpdf_installed = False

def serialize_rtip_export(session, user, itip, rtip, context, language):
    rtip_dict = serializers.serialize_rtip(session, itip, rtip, language)

    return {
        'type': 'export_template',
        'node': db_admin_serialize_node(session, user.tid, language),
        'notification': db_get_notification(session, user.tid, language),
        'tip': rtip_dict,
        'crypto_tip_prv_key': Base64Encoder.decode(rtip.crypto_tip_prv_key),
        'deprecated_crypto_files_prv_key': Base64Encoder.decode(rtip.deprecated_crypto_files_prv_key),
        'user': user_serialize_user(session, user, language),
        'context': admin_serialize_context(session, context, language),
        'submission_statuses': db_get_submission_statuses(session, user.tid, language)
    }


@transact
def get_tip_export(session, tid, user_id, itip_id, language):
    user, context, itip, rtip = session.query(models.User, models.Context, models.InternalTip, models.ReceiverTip) \
                                       .filter(models.User.id == user_id,
                                               models.User.tid == tid,
                                               models.ReceiverTip.receiver_id == models.User.id,
                                               models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                               models.InternalTip.id == itip_id,
                                               models.Context.id == models.InternalTip.context_id).one_or_none()

    if not user:
        raise errors.ResourceNotFound

    rtip.last_access = datetime_now()
    if rtip.access_date == datetime_null():
        rtip.access_date = rtip.last_access

    if itip.status == 'new':
        db_update_submission_status(session, tid, user_id, itip, 'opened', None)

    return user.pgp_key_public, serialize_rtip_export(session, user, itip, rtip, context, language)


def create_pdf(input_text):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    fonts_directory = os.path.join('globaleaks', 'fonts')

    fonts_data = {
        'inter': 'inter.ttf',
        'noto_sans_arabic': 'noto-sans-arabic.ttf',
        'noto_sans_lao': 'noto-sans-lao.ttf',
        'noto_sans_hebrew': 'noto-sans-hebrew.ttf',
        'noto_sans_korean': 'noto-sans-korean.ttf',
        'noto_sans_japanese': 'noto-sans-japanese.ttf',
        'noto_sans_tamil': 'noto-sans-tamil.ttf',
        'noto_sans_thai': 'noto-sans-thai.ttf',
        'noto_sans_bengali': 'noto-sans-bengali.ttf',
        'noto_sans_georgian': 'noto-sans-georgian.ttf',
        'noto_sans_tibetan': 'noto-sans-tibetan.ttf',
        'noto_sans_khmer': 'noto-sans-khmer.ttf',
        'noto_sans_armenian': 'noto-sans-armenian.ttf',
        'noto_sans_myanmar': 'noto-sans-myanmar.ttf',
        'noto_sans_thaana': 'noto-sans-thaana.ttf',
        'noto_sans_ethiopic': 'noto-sans-ethiopic.ttf',
    }

    # Register fonts with the PDF
    for font_key, font_file in fonts_data.items():
        pdf.add_font(family=font_key.upper(), style='', fname=os.path.join(fonts_directory, font_file))

    pdf.set_font('INTER')
    pdf.set_fallback_fonts([font_key.upper() for font_key in fonts_data if font_key != 'inter'])

    pdf.set_auto_page_break(auto=True, margin=15)
    line_height = 3
    margin = 10

    pdf.set_right_margin(margin)
    pdf.set_left_margin(margin)
    pdf.set_font_size(12)
    pdf.add_page()

    pdf.set_text_shaping(use_shaping_engine=True, direction="rtl")

    # Process each line
    for line in input_text.split('\n'):

        if any('\u0590' <= char <= '\u06FF' for char in line):  # Check for characters in Hebrew or Arabic blocks
            pdf.set_text_shaping(use_shaping_engine=True, direction="rtl")
        else:
            pdf.set_text_shaping(use_shaping_engine=True, direction="ltr")

        pdf.set_font('INTER')
        pdf.multi_cell(0, line_height, line.strip(), align='L')
        pdf.ln()

    # Generate PDF output as a bytearray
    pdf_output = pdf.output()
    output_buffer = io.BytesIO(pdf_output)
    output_buffer.seek(0)
    return output_buffer.getvalue()

@inlineCallbacks
def prepare_tip_export(user_session, tip_export):
    tip_export['tip']['rfiles'] = list(filter(lambda x: x['visibility'] != 'personal', tip_export['tip']['rfiles']))

    files = tip_export['tip']['wbfiles'] + tip_export['tip']['rfiles']

    if tip_export['crypto_tip_prv_key']:
        tip_export['tip'] = yield deferToThread(decrypt_tip, user_session.cc, tip_export['crypto_tip_prv_key'], tip_export['tip'])

        tip_export['tip'] = yield redact_report(user_session.user_id, tip_export['tip'], True)

        for file_dict in tip_export['tip']['wbfiles']:
            if tip_export['deprecated_crypto_files_prv_key']:
                files_prv_key = GCE.asymmetric_decrypt(user_session.cc, tip_export['deprecated_crypto_files_prv_key'])
            else:
                files_prv_key = GCE.asymmetric_decrypt(user_session.cc, tip_export['crypto_tip_prv_key'])

            filelocation = os.path.join(Settings.attachments_path, file_dict['id'])
            if not os.path.exists(filelocation):
                filelocation = os.path.join(Settings.attachments_path, file_dict['ifile_id'])

            directory_traversal_check(Settings.attachments_path, filelocation)
            file_dict['key'] = files_prv_key
            file_dict['path'] = filelocation
            del filelocation

        for file_dict in tip_export['tip']['rfiles']:
            tip_prv_key = GCE.asymmetric_decrypt(user_session.cc, tip_export['crypto_tip_prv_key'])
            filelocation = os.path.join(Settings.attachments_path, file_dict['id'])
            directory_traversal_check(Settings.attachments_path, filelocation)
            file_dict['key'] = tip_prv_key
            file_dict['path'] = filelocation
            del filelocation

    for file_dict in tip_export['tip'].pop('wbfiles'):
        file_dict['name'] = 'files/' + file_dict['name']
        if file_dict.get('status', '') == 'encrypted':
            file_dict['name'] += '.pgp'

    for file_dict in tip_export['tip'].pop('rfiles'):
        file_dict['name'] = 'files_attached_from_recipients/' + file_dict['name']

    tip_export['comments'] = tip_export['tip']['comments']

    export_template = Templating().format_template(tip_export['notification']['export_template'], tip_export).encode()
    export_template = msdos_encode(export_template.decode()).encode()

    if fpdf_installed:
        pdf_bytes = create_pdf(export_template.decode())
        files.append({'fo': BytesIO(pdf_bytes), 'name': 'report.pdf'})
    else:
        files.append({'fo': BytesIO(export_template), 'name': 'report.txt'})

    return files


class ExportHandler(BaseHandler):
    check_roles = 'receiver'
    handler_exec_time_threshold = 3600

    @inlineCallbacks
    def get(self, itip_id):
        pgp_key, tip_export = yield get_tip_export(self.request.tid,
                                                   self.session.user_id,
                                                   itip_id,
                                                   self.request.language)

        filename = "report-" + str(tip_export["tip"]["progressive"]) + ".zip"

        files = yield prepare_tip_export(self.session, tip_export)

        zipstream = ZipStream(files)

        stf = SecureTemporaryFile(self.state.settings.tmp_path)

        with stf.open('w') as f:
            for x in zipstream:
                f.write(x)
            f.finalize_write()

        with stf.open('r') as f:
            yield self.write_file_as_download(filename, f, pgp_key)