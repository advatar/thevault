from kay.utils.forms.modelform import ModelForm
from core.models import ConsumerApp

class ConsumerAppForm(ModelForm):
    class Meta:
        model = ConsumerApp
        exclude = (
            'created_at',
            'updated_at',
            'user',
            'consumer_key',
            'consumer_secret', )
