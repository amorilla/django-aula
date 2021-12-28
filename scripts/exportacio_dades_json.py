from django.core.serializers import serialize
from aula.apps.assignatures.models import TipusDAssignatura
from aula.apps.extEsfera.models import ParametreEsfera
from aula.apps.extSaga.models import ParametreSaga
from aula.apps.extKronowin.models import ParametreKronowin
from aula.apps.horaris.models import FranjaHoraria, DiaDeLaSetmana
from aula.apps.incidencies.models import FrassesIncidenciaAula, TipusSancio, TipusIncidencia
from aula.apps.presencia.models import EstatControlAssistencia
from django.contrib.auth.models import Group
from aula.apps.sortides.models import TPV, Quota

def exportJson(dades, app):
    f= open("./aula/apps/"+app+"/fixtures/dades.json","w+")
    f.write(dades)
    f.close() 

dades=serialize('json', TipusDAssignatura.objects.all())
exportJson(dades,'assignatures')
dades=serialize('json', ParametreEsfera.objects.all())
exportJson(dades,'extEsfera')
dades=serialize('json', ParametreSaga.objects.all())
exportJson(dades,'extSaga')
dades=serialize('json', ParametreKronowin.objects.all())
exportJson(dades,'extKronowin')
dades=serialize('json', FranjaHoraria.objects.all())
dades=dades[:len(dades)-1]+","+serialize('json', DiaDeLaSetmana.objects.all())[1:]
exportJson(dades,'horaris')
dades=serialize('json', FrassesIncidenciaAula.objects.all())
dades=dades[:len(dades)-1]+","+serialize('json', TipusSancio.objects.all())[1:]
dades=dades[:len(dades)-1]+","+serialize('json', TipusIncidencia.objects.all())[1:]
exportJson(dades,'incidencies')
dades=serialize('json', EstatControlAssistencia.objects.all())
exportJson(dades,'presencia')
dades=serialize('json', Group.objects.all())
exportJson(dades,'usuaris')
dades=serialize('json', TPV.objects.all())
dades=dades[:len(dades)-1]+","+serialize('json', Quota.objects.all())[1:]
exportJson(dades,'sortides')


quit()
