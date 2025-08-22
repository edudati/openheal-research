from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None or password is None:
            return None
        try:
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.MultipleObjectsReturned:
            # se houver duplicidade de e-mail, prioriza username exato
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                return None
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
