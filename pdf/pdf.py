""" pdfXBlock main Python class"""

import pkg_resources
from django.template import Context, Template

from xblock.core import XBlock
from xblock.fields import Scope, String, Boolean, Integer
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from .utils import _, bool_from_str, DummyTranslationService, is_all_download_disabled

loader = ResourceLoader(__name__)


@XBlock.needs('i18n')
class PdfBlock(XBlock):

    '''
    Icon of the XBlock. Values : [other (default), video, problem]
    '''
    icon_class = "other"

    '''
    Fields
    '''
    display_name = String(
        display_name=_("Display Name"),
        default=_("PDF"),
        scope=Scope.settings,
        help=_("This name appears in the horizontal navigation at the top of the page.")
    )

    url = String(
        display_name=_("PDF URL"),
        default=_("https://tutorial.math.lamar.edu/pdf/Trig_Cheat_Sheet.pdf"),
        scope=Scope.content,
        help=_("The URL for your PDF.")
    )

    pdf_height = Integer(
        display_name=_("PDF Height"),
        default=600,  # Default height
        scope=Scope.settings,
        help=_("The height of the PDF viewer in pixels.")
    )

    allow_download = Boolean(
        display_name=_("PDF Download Allowed"),
        default=True,
        scope=Scope.content,
        help=_("Display a download button for this PDF.")
    )

    source_text = String(
        display_name=_("Source document button text"),
        default="",
        scope=Scope.content,
        help=_(
            "Add a download link for the source file of your PDF. "
             "Use it for example to provide the PowerPoint file used to create this PDF."
        )
    )

    source_url = String(
        display_name=_("Source document URL"),
        default="",
        scope=Scope.content,
        help=_(
            "Add a download link for the source file of your PDF. "
             "Use it for example to provide the PowerPoint file used to create this PDF."
        )
    )

    '''
    Util functions
    '''
    def load_resource(self, resource_path):
        """
        Gets the content of a resource
        """
        resource_content = pkg_resources.resource_string(__name__, resource_path)
        return resource_content.decode("utf8")

    def render_template(self, template_path, context={}):
        """
        Evaluate a template by resource path, applying the provided context
        """
        template_str = self.load_resource(template_path)
        return Template(template_str).render(Context(context))

    '''
    Main functions
    '''
    def student_view(self, context=None):
        """
        The primary view of the XBlock, shown to students
        when viewing courses.
        """
        context = {
            'display_name': self.display_name,
            'url': self.url,
            'pdf_height': self.pdf_height,
            'allow_download': self.allow_download,
            'disable_all_download': is_all_download_disabled(),
            'source_text': self.source_text,
            'source_url': self.source_url,
            '_i18n_service': self.i18n_service,
        }
        html = loader.render_django_template(
            'templates/html/pdf_view.html',
            context=context,
            i18n_service=self.i18n_service,
        )

        event_type = 'edx.pdf.loaded'
        event_data = {
            'url': self.url,
            'source_url': self.source_url,
        }
        self.runtime.publish(self, event_type, event_data)
        frag = Fragment(html)
        frag.add_javascript(self.load_resource("static/js/pdf_view.js"))
        frag.initialize_js('pdfXBlockInitView')
        return frag

    def studio_view(self, context=None):
        """
        The secondary view of the XBlock, shown to teachers
        when editing the XBlock.
        """
        context = {
            'display_name': self.display_name,
            'url': self.url,
            'allow_download': self.allow_download,
            'disable_all_download': is_all_download_disabled(),
            'source_text': self.source_text,
            'source_url': self.source_url
        }
        html = loader.render_django_template(
            'templates/html/pdf_edit.html',
            context=context,
            i18n_service=self.i18n_service,
        )
        frag = Fragment(html)
        frag.add_javascript(self.load_resource("static/js/pdf_edit.js"))
        frag.initialize_js('pdfXBlockInitEdit')
        return frag

    @XBlock.json_handler
    def on_download(self, data, suffix=''):
        """
        The download file event handler
        """
        event_type = 'edx.pdf.downloaded'
        event_data = {
            'url': self.url,
            'source_url': self.source_url,
        }
        self.runtime.publish(self, event_type, event_data)

    @XBlock.json_handler
    def save_pdf(self, data, suffix=''):
        """
        The saving handler.
        """
        self.display_name = data['display_name']
        self.url = data['url']

        if not is_all_download_disabled():
            self.allow_download = bool_from_str(data['allow_download'])
            self.source_text = data['source_text']
            self.source_url = data['source_url']

        return {
            'result': 'success',
        }

    @property
    def i18n_service(self):
        """ Obtains translation service """
        i18n_service = self.runtime.service(self, "i18n")
        if i18n_service:
            return i18n_service
        else:
            return DummyTranslationService()
