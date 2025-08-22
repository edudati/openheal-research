from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from .models import Study, Researcher, Participant, Match
from .forms import AdminUserCreationForm, AdminUserChangeForm, ParticipantAdminForm
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import messages
from django.db import transaction
from .services.openheal_matches import sync_matches_for_participant
from django.contrib import admin


admin.site.site_header = "Researcher - OpenHeal"
admin.site.site_title = "OpenHeal Researcher"
admin.site.index_title = "Connect Matches"
admin.site.site_url = None


# --- Apenas super pode criar/editar Study ---
@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "is_active", "start_date", "end_date")
    ordering = ("title", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "title")
    readonly_fields = ("quick_actions",)  # mostra na página do estudo
    fields = ("code", "title", "description", "start_date", "end_date", "is_active", "quick_actions")

    def quick_actions(self, obj):
        if not obj:
            return "-"
        add_url  = reverse("admin:research_admin_participant_add") + f"?study={obj.pk}"
        list_url = reverse("admin:research_admin_participant_changelist") + f"?study__id__exact={obj.pk}"
        return format_html(
            '<a class="button" href="{}">Add participant</a> &nbsp;|&nbsp; <a href="{}">View participants</a>',
            add_url, list_url
        )
    quick_actions.short_description = "Quick actions"

    # (mantém as permissões que já definiu)
    def has_module_permission(self, request): return True
    def has_view_permission(self, request, obj=None): return True
    def has_add_permission(self, request): return request.user.is_superuser
    def has_change_permission(self, request, obj=None): return request.user.is_superuser
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser


# --- Apenas super gerencia Researcher ---
@admin.register(Researcher)
class ResearcherAdmin(admin.ModelAdmin):
    list_display = ("user", "institution")
    filter_horizontal = ("studies",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "institution")

    def has_module_permission(self, request): return request.user.is_superuser
    def has_view_permission(self, request, obj=None): return request.user.is_superuser
    def has_add_permission(self, request): return request.user.is_superuser
    def has_change_permission(self, request, obj=None): return request.user.is_superuser
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser


# --- Mixin para escopo por Study ---
class StudyScopedAdminMixin:
    study_fk_name = "study"  # para modelos com FK direto para Study

    def user_allowed_studies(self, request):
        if request.user.is_superuser:
            return Study.objects.all()
        try:
            researcher = Researcher.objects.get(user=request.user)
            return researcher.studies.all()
        except Researcher.DoesNotExist:
            return Study.objects.none()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        allowed = self.user_allowed_studies(request)
        field_names = [f.name for f in qs.model._meta.fields]

        if self.study_fk_name in field_names:
            return qs.filter(**{f"{self.study_fk_name}__in": allowed})

        if self.study_fk_name == "participant__study":
            return qs.filter(participant__study__in=allowed)

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "study":
            kwargs["queryset"] = self.user_allowed_studies(request)
        if db_field.name == "participant":
            kwargs["queryset"] = Participant.objects.filter(study__in=self.user_allowed_studies(request))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# --- Filtros por Researcher (convertendo para Study) ---
class ResearcherStudyFilterForParticipants(admin.SimpleListFilter):
    title = "researcher"
    parameter_name = "by_researcher"

    def lookups(self, request, model_admin):
        qs = Researcher.objects.all() if request.user.is_superuser else Researcher.objects.filter(user=request.user)
        return [(str(r.pk), r.user.get_full_name() or r.user.username) for r in qs]

    def queryset(self, request, queryset):
        val = self.value()
        if not val:
            return queryset
        try:
            r = Researcher.objects.get(pk=val)
            return queryset.filter(study__in=r.studies.all())
        except Researcher.DoesNotExist:
            return queryset.none()


class ResearcherStudyFilterForMatches(admin.SimpleListFilter):
    title = "researcher"
    parameter_name = "by_researcher"

    def lookups(self, request, model_admin):
        qs = Researcher.objects.all() if request.user.is_superuser else Researcher.objects.filter(user=request.user)
        return [(str(r.pk), r.user.get_full_name() or r.user.username) for r in qs]

    def queryset(self, request, queryset):
        val = self.value()
        if not val:
            return queryset
        try:
            r = Researcher.objects.get(pk=val)
            return queryset.filter(participant__study__in=r.studies.all())
        except Researcher.DoesNotExist:
            return queryset.none()


# --- Inline de Match dentro do Participant ---
# Inline na página do Participant
class MatchInline(admin.TabularInline):
    model = Match
    extra = 0
    can_delete = False
    show_change_link = True
    readonly_fields = ("id","preset_id","level_id","result_id","date", "screen_size")
    fields = ("id","preset_id","level_id","result_id","date",
              "phase_id","intervention_id","moment_id", "screen_size", "is_active","is_used")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        # Permite edição para superusuários e pesquisadores dos estudos permitidos
        if request.user.is_superuser:
            return True
        # Para pesquisadores, verifica se têm acesso ao estudo do participante
        if obj:
            return obj.study in self.get_user_allowed_studies(request)
        return True
    
    def get_user_allowed_studies(self, request):
        if request.user.is_superuser:
            return Study.objects.all()
        try:
            researcher = Researcher.objects.get(user=request.user)
            return researcher.studies.all()
        except Researcher.DoesNotExist:
            return Study.objects.none()

# Admin de Match
@admin.register(Match)
class MatchAdmin(StudyScopedAdminMixin, admin.ModelAdmin):
    study_fk_name = "participant__study"
    list_display = (
        "id","participant","preset_id","level_id","phase_id",
        "intervention_id","moment_id","result_id","date", "screen_size", "is_active","is_used"
    )
    list_editable = ("phase_id", "intervention_id", "moment_id", "is_active", "is_used")
    search_fields = ("id","participant__id","participant__name","result_id")
    list_filter = ("is_active","is_used","participant","date", ResearcherStudyFilterForMatches)
    date_hierarchy = "date"
    autocomplete_fields = ("participant",)
    readonly_fields = ("id","participant","preset_id","level_id","result_id","date", "screen_size")
    
    def has_add_permission(self, request): 
        return False
    
    def has_change_permission(self, request, obj=None):
        # Permite edição para superusuários e pesquisadores dos estudos permitidos
        if request.user.is_superuser:
            return True
        # Para pesquisadores, verifica se têm acesso ao estudo da match
        if obj:
            return obj.participant.study in self.user_allowed_studies(request)
        return True  # Para list view, permite se tiver acesso aos estudos
    
    def has_delete_permission(self, request, obj=None): 
        return False



# --- Participant ---
@admin.register(Participant)
class ParticipantAdmin(StudyScopedAdminMixin, admin.ModelAdmin):
    form = ParticipantAdminForm
    list_display = ("id", "name", "email", "group", "study")
    search_fields = ("id", "name", "email")
    list_filter = ("group", "study", ResearcherStudyFilterForParticipants)
    autocomplete_fields = ("study",)
    inlines = [MatchInline]
    readonly_fields = ("id",)
    ordering = ("name", "id")

    # no create: oculta o campo id; na edição: mostra id somente leitura
    def get_fields(self, request, obj=None):
        base = ["study", "name", "email", "group"]
        return ["id"] + base if obj else base

    # prefill do estudo se vier ?study=<id> na URL
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if "study" in request.GET:
            initial["study"] = request.GET.get("study")
        return initial
    

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:  # foi criado agora
            transaction.on_commit(lambda: self._sync_and_notify(request, obj))

    def _sync_and_notify(self, request, obj):
        created = sync_matches_for_participant(obj)
        messages.success(request, f"Matches criadas: {created}")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and request.method == "GET":
            try:
                created = sync_matches_for_participant(obj)
                if created:
                    self.message_user(request, f"Sincronizadas {created} novas matches.", level=messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"Falha ao sincronizar matches: {e}", level=messages.ERROR)
        return super().change_view(request, object_id, form_url, extra_context)
    
    def has_delete_permission(self, request, obj=None): return True


# --- UserAdmin (ÚNICA definição + registro no final) ---
class UserAdmin(DjangoUserAdmin):
    add_form = AdminUserCreationForm
    form = AdminUserChangeForm

    list_display = ("username", "email", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email")
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2",
                       "is_staff", "is_superuser", "is_active"),
        }),
    )

    # Restringe gestão de usuários a super
    def has_module_permission(self, request): return request.user.is_superuser
    def has_view_permission(self, request, obj=None): return request.user.is_superuser
    def has_add_permission(self, request): return request.user.is_superuser
    def has_change_permission(self, request, obj=None): return request.user.is_superuser
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser


# Registrar o UserAdmin (após a classe final)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
