from django.core.files.storage import default_storage
from django.utils.functional import lazy
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers, fields

from baserow.contrib.database.export.handler import ExportHandler
from baserow.contrib.database.export.models import ExportJob
from baserow.contrib.database.export.registries import table_exporter_registry

# This is a map from the front end supported charsets to the internal python supported
# charset value as they do not always match up.
# Please keep in sync with
# web-frontend/modules/core/components/helpers/CharsetDropdown.vue:
SUPPORTED_EXPORT_CHARSETS = [
    ("utf-8", "utf-8"),
    ("iso-8859-6", "iso-8859-6"),
    ("windows-1256", "windows-1256"),
    ("iso-8859-4", "iso-8859-4"),
    ("windows-1257", "windows-1257"),
    ("iso-8859-14", "iso-8859-14"),
    ("iso-8859-2", "iso-8859-2"),
    ("windows-1250", "windows-1250"),
    ("gbk", "gbk"),
    ("gb18030", "gb18030"),
    ("big5", "big5"),
    ("koi8-r", "koi8-r"),
    ("koi8-u", "koi8-u"),
    ("iso-8859-5", "iso-8859-5"),
    ("windows-1251", "windows-1251"),
    ("x-mac-cyrillic", "mac-cyrillic"),
    ("iso-8859-7", "iso-8859-7"),
    ("windows-1253", "windows-1253"),
    ("iso-8859-8", "iso-8859-8"),
    ("windows-1255", "windows-1255"),
    ("euc-jp", "euc-jp"),
    ("iso-2022-jp", "iso-2022-jp"),
    ("shift-jis", "shift-jis"),
    ("euc-kr", "euc-kr"),
    ("macintosh", "macintosh"),
    ("iso-8859-10", "iso-8859-10"),
    ("iso-8859-16", "iso-8859-16"),
    ("windows-874", "cp874"),
    ("windows-1254", "windows-1254"),
    ("windows-1258", "windows-1258"),
    ("iso-8859-1", "iso-8859-1"),
    ("windows-1252", "windows-1252"),
    ("iso-8859-3", "iso-8859-3"),
]
# Please keep in sync with modules/database/components/export/TableCSVExporter.vue
SUPPORTED_CSV_COLUMN_SEPARATORS = [
    (",", ","),
    (";", ";"),
    ("|", "|"),
    ("tab", "\t"),
    ("record_separator", "\x1e"),
    ("unit_separator", "\x1f"),
]


class ExportedFileURLSerializerMixin(serializers.Serializer):
    """
    When mixed in to a model serializer for an ExportJob this will add an url field
    with the actual usable url of the export job's file (if it has one).
    """

    url = serializers.SerializerMethodField()

    def get_instance_attr(self, instance, name):
        return getattr(instance, name)

    @extend_schema_field(OpenApiTypes.URI)
    def get_url(self, instance):
        name = self.get_instance_attr(instance, "exported_file_name")
        if name:
            path = ExportHandler().export_file_path(name)
            return default_storage.url(path)
        else:
            return None


class ExportJobSerializer(ExportedFileURLSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ExportJob
        fields = [
            "id",
            "table",
            "view",
            "exporter_type",
            "status",
            "exported_file_name",
            "expires_at",
            "progress_percentage",
            "url",
        ]


class DisplayChoiceField(serializers.ChoiceField):
    """
    Just like a choice field but returns the second value of each choice tuple when
    serialized.
    """

    def to_representation(self, obj):
        return self._choices[obj]


class BaseExporterOptionsSerializer(serializers.Serializer):
    exporter_type = fields.ChoiceField(
        choices=lazy(table_exporter_registry.get_types, list)()
    )
    # Map to the python encoding aliases at the same time by using a DisplayChoiceField
    export_charset = DisplayChoiceField(
        choices=SUPPORTED_EXPORT_CHARSETS, default="utf-8"
    )


class CsvExporterOptionsSerializer(BaseExporterOptionsSerializer):
    # For ease of use we expect the JSON to contain human typeable forms of each
    # different separator instead of the unicode character itself. By using the
    # DisplayChoiceField we can then map this to the actual separator character by
    # having those be the second value of each choice tuple.
    csv_column_separator = DisplayChoiceField(
        choices=SUPPORTED_CSV_COLUMN_SEPARATORS, default=","
    )
    csv_include_header = fields.BooleanField(default=True)