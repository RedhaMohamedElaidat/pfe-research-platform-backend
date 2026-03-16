from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
import re


class AdminRole(models.TextChoices):
    SUPER_ADMIN  = 'Super_Admin',  'Super Admin'
    DATA_MANAGER = 'Data_Manager', 'Data Manager'


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        user  = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    user_id    = models.AutoField(primary_key=True)
    username   = models.CharField(max_length=150, unique=True)
    email      = models.EmailField(unique=True)
    password   = models.CharField(max_length=128)
    first_name = models.CharField(max_length=30, blank=True)
    last_name  = models.CharField(max_length=30, blank=True)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects         = UserManager()
    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table        = 'users'
        verbose_name    = 'User'
        verbose_name_plural = 'Users'

    def check_password(self, raw_password):
        return super().check_password(raw_password)

    def __str__(self):
        return f"{self.username} - {self.email}"


class Admin(models.Model):
    """
    Deux rôles possibles :
    ┌─────────────────┬──────────────────────────────────────────────────────┐
    │ Super_Admin     │ Gère les utilisateurs + valide les données           │
    │ Data_Manager    │ Valide les données uniquement (pas de gestion users) │
    └─────────────────┴──────────────────────────────────────────────────────┘
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    role = models.CharField(max_length=20, choices=AdminRole.choices, default=AdminRole.DATA_MANAGER)

    class Meta:
        db_table        = 'admins'
        verbose_name    = 'Admin'
        verbose_name_plural = 'Admins'

    # ── Permissions ────────────────────────────────────────────────────────
    @property
    def is_super_admin(self) -> bool:
        return self.role == AdminRole.SUPER_ADMIN

    @property
    def is_data_manager(self) -> bool:
        return self.role == AdminRole.DATA_MANAGER

    # ── Actions Super_Admin uniquement ─────────────────────────────────────
    def manage_users(self):
        """Liste tous les utilisateurs actifs. Réservé au Super_Admin."""
        if not self.is_super_admin:
            raise PermissionError("Seul le Super Admin peut gérer les utilisateurs.")
        return User.objects.filter(is_active=True)

    def deactivate_user(self, user: User):
        """Désactive un compte utilisateur. Réservé au Super_Admin."""
        if not self.is_super_admin:
            raise PermissionError("Seul le Super Admin peut désactiver un utilisateur.")
        user.is_active = False
        user.save(update_fields=['is_active'])

    def activate_user(self, user: User):
        """Réactive un compte utilisateur. Réservé au Super_Admin."""
        if not self.is_super_admin:
            raise PermissionError("Seul le Super Admin peut activer un utilisateur.")
        user.is_active = True
        user.save(update_fields=['is_active'])

    # ── Actions Data_Manager + Super_Admin ─────────────────────────────────
    def validate_data(self, publication):
        """Valide une publication. Accessible aux deux rôles."""
        publication.validate()

    def reject_data(self, publication):
        """Rejette une publication (remet is_validated à False)."""
        publication.is_validated = False
        publication.save(update_fields=['is_validated'])

    def __str__(self):
        return f"Admin: {self.user.username} | Role: {self.get_role_display()}"


def validate_orcid(value):
    """Validateur ORCID format XXXX-XXXX-XXXX-XXXX."""
    from django.core.exceptions import ValidationError
    pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
    if value and not re.match(pattern, value):
        raise ValidationError(f"Format ORCID invalide : '{value}'. Attendu : XXXX-XXXX-XXXX-XXXX")


class Researcher(models.Model):
    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='researcher_profile')
    orcid          = models.CharField(max_length=19, unique=True, blank=True, null=True, validators=[validate_orcid])
    research_field = models.CharField(max_length=255, blank=True)
    h_index        = models.IntegerField(default=0)

    class Meta:
        db_table        = 'researchers'
        verbose_name    = 'Researcher'
        verbose_name_plural = 'Researchers'

    def __str__(self):
        return (
            f"Researcher: {self.user.username} - {self.user.get_full_name()} "
            f"| ORCID: {self.orcid} | H-index: {self.h_index} | Field: {self.research_field}"
        )

    def calculate_h_index(self) -> int:
        """Calcule et met à jour le h-index du chercheur."""
        citation_counts = [
            coauth.publication.get_citation_count()
            for coauth in self.user.coauthored_publications.select_related('publication')
        ]
        citation_counts.sort(reverse=True)

        h = 0
        for i, citations in enumerate(citation_counts, start=1):
            if citations >= i:
                h = i
            else:
                break

        self.h_index = h
        self.save(update_fields=['h_index'])
        return h


class LabManager(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lab_manager_profile')
    laboratory = models.ForeignKey('laboratory.Laboratory', on_delete=models.CASCADE, related_name='lab_managers')
    start_date = models.DateField(default=timezone.now)
    end_date   = models.DateField(blank=True, null=True)

    class Meta:
        db_table        = 'lab_managers'
        verbose_name    = 'Lab Manager'
        verbose_name_plural = 'Lab Managers'

    def __str__(self):
        return f"Lab Manager: {self.user.username} - {self.user.get_full_name()} - Lab: {self.laboratory.name}"


class TeamLeader(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team_leader_profile')
    team       = models.ForeignKey('team.Team', on_delete=models.CASCADE, related_name='team_leaders')
    start_date = models.DateField(default=timezone.now)
    end_date   = models.DateField(blank=True, null=True)

    class Meta:
        db_table        = 'team_leaders'
        verbose_name    = 'Team Leader'
        verbose_name_plural = 'Team Leaders'

    def __str__(self):
        return f"Team Leader: {self.user.username} - {self.user.get_full_name()} - Team: {self.team.name}"