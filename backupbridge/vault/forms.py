from kay.utils.forms.modelform import ModelForm
from vault.models import Vault

class ReleaseForm(ModelForm):
    class Meta:
        model = Vault
        exclude = (
            'created_at',)
