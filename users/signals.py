# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import Researcher
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Researcher)
def sync_on_orcid_added(sender, instance, created, update_fields, **kwargs):
    """
    Déclenche automatiquement la sync OpenAlex
    quand un ORCID est ajouté ou modifié.
    """
    # Ne lancer que si l'ORCID vient d'être renseigné
    if not instance.orcid:
        return

    # Eviter les boucles infinies — ne lancer que si orcid a changé
    if update_fields and 'orcid' not in update_fields:
        return

    try:
        from data_pipeline.openalex_researcher_sync import sync_researcher
        logger.info(f"Signal → sync OpenAlex pour ORCID: {instance.orcid}")
        sync_researcher(instance.orcid)
    except Exception as e:
        logger.error(f"Erreur signal sync ORCID {instance.orcid}: {e}")