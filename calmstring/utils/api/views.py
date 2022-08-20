class LogicAPIView:

    DETAIL_KEY = "detail"

    def validate(self):
        """Runs serializer validation and creates self.serializer property"""
        self.serializer = self.get_serializer_class()(data=self.request.data)
        self.serializer.is_valid(raise_exception=True)

    def create(self, *args, **kwargs):
        self.validate()
        self.validated_data = self.serializer.validated_data

    def update(self, *args, **kwargs):
        self.serializer = self.get_serializer_class()(
            self.get_object(), data=self.request.data
        )
        self.serializer.is_valid(raise_exception=True)
        self.validated_data = self.serializer.validated_data
        self.object = self.get_object()

    def partial_update(self, *args, **kwargs):
        self.serializer = self.get_serializer_class()(
            self.get_object(), data=self.request.data, partial=True
        )
        self.serializer.is_valid(raise_exception=True)
        self.validated_data = self.serializer.validated_data
        self.object = self.get_object()
