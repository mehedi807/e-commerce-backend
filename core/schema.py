from drf_spectacular.openapi import AutoSchema


class ApiAutoSchema(AutoSchema):
    def get_description(self):
        if hasattr(self.view, "description"):
            if isinstance(self.view.description, dict):
                return self.view.description.get(self.method)
            return self.view.description
        return super().get_description()

    def get_request_serializer(self):
        if hasattr(self.view, "InputSerializer"):
            return self.view.InputSerializer
        return super().get_request_serializer()

    def get_response_serializers(self):
        if hasattr(self.view, "OutputSerializer"):
            return self.view.OutputSerializer
        return super().get_response_serializers()
