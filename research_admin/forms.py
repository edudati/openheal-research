from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import Participant
from .services.openheal_lookup import get_openheal_id_by_email

class ParticipantAdminForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ("study", "name", "email", "group")  # sem "id" no formulário

    def clean(self):
        cleaned = super().clean()
        # Só no create (sem PK ainda)
        if not self.instance.pk:
            email = cleaned.get("email")
            openheal_id = get_openheal_id_by_email(email)
            if not openheal_id:
                raise ValidationError("OpenHeal ID não encontrado para este e-mail no banco externo.")
            # define a PK antes de salvar
            self.instance.id = str(openheal_id)
        return cleaned


class _UniqueEmailMixin:
    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            return email
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class AdminUserCreationForm(_UniqueEmailMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "is_staff", "is_superuser", "is_active")


class AdminUserChangeForm(_UniqueEmailMixin, UserChangeForm):
    class Meta:
        model = User
        fields = (
            "username", "email", "first_name", "last_name",
            "is_staff", "is_superuser", "is_active",
            "groups", "user_permissions",
        )
