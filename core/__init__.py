def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if self.instance and self.instance.pk:
        self.set_dynamic_field(self.instance)
