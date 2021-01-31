from django.conf.urls import url
from django.conf import settings
from aula.apps.matricula.views import peticio, PeticioVerifica, PeticiobyId, \
            OmpleDades, LlistaMat, changeEstat, condicions, LlistaMatFinals, DadesbyId, \
            AcceptaCondicions
            
app_name = 'matricula'

urlpatterns = [
                       
    url(r'^peticio/$', peticio, name="peticio"),
    url(r'^verifica/$', PeticioVerifica, name='gestio__peticions__pendents'),
    url(r'^verifica/(?P<pk>\d+)$', PeticiobyId, name='gestio__peticions__pendents'),
    url(r'^accepta/$', AcceptaCondicions, name='relacio_families__matricula__accepta'),
    url(r'^dades/$', OmpleDades, name='relacio_families__matricula__dades'),
    url(r'^dades/(?P<pk>\d+)$', DadesbyId, name='gestio__confirma__matricula'),
    url(r'^matricula/$', LlistaMat, name='gestio__confirma__matricula'),
    url(r'^matfinals/$', LlistaMatFinals, name='gestio__llistat__matricula'),
    url(r'^changeestat/(?P<pk>\d+)$', changeEstat, name='changeestat'),
    url(r'^condicions/$', condicions, name ="varis__condicions__matricula" )    ,

]

if not settings.CUSTOM_MODUL_MATRICULA_ACTIU:
    urlpatterns = urlpatterns[1:]
