from django import template
from aula.apps.extPreinscripcio.models import Preinscripcio

register = template.Library()

@register.filter(name='torn')
def getTorn(peticio):
    return Preinscripcio.objects.get(ralc=peticio.alumne.ralc).torn
