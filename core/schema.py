from drf_spectacular.openapi import AutoSchema

class ApiAutoSchema(AutoSchema):
    def get_description(self):
        if hasattr(self.view, "description"):
            if isinstance(self.view.description, dict):
                return self.view.description.get(self.method)
            return self.view.description
        return super().get_description()

    def _set_ref_name(self, serializer_class, ref_name):
        if not hasattr(serializer_class, 'Meta'):
            class Meta:
                pass
            serializer_class.Meta = Meta

        serializer_class.Meta.ref_name = ref_name
        return serializer_class

    def get_request_serializer(self):
        if hasattr(self.view, 'InputSerializer'):
            return self._set_ref_name(
                self.view.InputSerializer,
                f'{self.view.__class__.__name__}InputSerializer',
            )
        return super().get_request_serializer()

    def get_response_serializers(self):
        if hasattr(self.view, 'OutputSerializer'):
            return self._set_ref_name(
                self.view.OutputSerializer,
                f'{self.view.__class__.__name__}OutputSerializer',
            )
        return super().get_response_serializers()
