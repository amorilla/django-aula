from django import template
from aula.apps.extPreinscripcio.models import Preinscripcio
from aula.apps.sortides.models import QuotaPagament
from django.conf import settings

register = template.Library()

@register.filter(name='torn')
def getTorn(peticio):
    return Preinscripcio.objects.get(ralc=peticio.alumne.ralc).torn

@register.filter(name='nomesFracc')
def nomesFracc(peticio):
    pagmat=QuotaPagament.objects.filter(alumne=peticio.alumne, quota__any=peticio.any,
                             quota__tipus__nom=settings.CUSTOM_TIPUS_QUOTA_MATRICULA)
    pagtax=QuotaPagament.objects.filter(alumne=peticio.alumne, quota__any=peticio.any,
                             quota__tipus=peticio.curs.nivell.taxes)
    if peticio.dades:
        if peticio.dades.fracciona_taxes and pagtax and pagtax.count()==2:
            return pagmat[0].pagament_realitzat and ((pagtax[0].pagament_realitzat and not pagtax[1].pagament_realitzat) \
                    or (not pagtax[0].pagament_realitzat and pagtax[1].pagament_realitzat))
        else:
            return False
    else:
        return False 
