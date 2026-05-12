import logging
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage

logger = logging.getLogger(__name__)


class LenientManifestStaticFilesStorage(ManifestStaticFilesStorage):
    manifest_strict = False

    def url_converter(self, name, hashed_files, template=None):
        converter = super().url_converter(name, hashed_files, template)

        def safe_converter(matchobj):
            try:
                return converter(matchobj)
            except ValueError as e:
                logger.warning("Skipping missing reference in %s: %s", name, e)
                return matchobj.group(0)

        return safe_converter