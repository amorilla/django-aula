from django import forms
from django.conf import settings
from aula.django_select2.forms import ModelSelect2Widget
from django.forms.models import ModelChoiceField
from aula.apps.alumnes.models import Curs
from aula.apps.sortides.models import Sortida, Quota, QuotaPagament, TipusQuota, TPV
import datetime

class PagamentForm(forms.Form):
    sortida = forms.CharField(widget=forms.HiddenInput())
    acceptar_condicions = forms.BooleanField(required=True)

    def __init__(self, *args, **kwargs):
        super(PagamentForm, self).__init__(*args, **kwargs)
        self.sortida = kwargs.pop('sortida', None)
        self.acceptar_condicions = False

TIPUS_INIT = Sortida.TIPUS_PAGAMENT_CHOICES
TIPUS_CHOICES = []
if not settings.CUSTOM_SORTIDES_PAGAMENT_ONLINE:
    for c in TIPUS_INIT:
        if (c[0]!='ON'): TIPUS_CHOICES.append(c)
else:
    TIPUS_CHOICES = TIPUS_INIT
        
TIPUS_INIT = TIPUS_CHOICES
TIPUS_CHOICES = []
if not settings.CUSTOM_SORTIDES_PAGAMENT_CAIXER:
    for c in TIPUS_INIT:
        if (c[0]!='EB'): TIPUS_CHOICES.append(c)
else:
    TIPUS_CHOICES = TIPUS_INIT

class SortidaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SortidaForm, self).__init__(*args, **kwargs)
        self.fields['tipus_de_pagament'].choices = TIPUS_CHOICES

def year_choices():
    '''
    Retorna choices d'anys possibles per als pagaments
    '''
    primer=QuotaPagament.objects.filter(data_hora_pagament__isnull=False).order_by('data_hora_pagament').first()
    ultim=QuotaPagament.objects.filter(data_hora_pagament__isnull=False).order_by('data_hora_pagament').last()
    if primer:
        primer = primer.data_hora_pagament.year
    else:
        primer=current_year()
    if ultim:
        ultim = ultim.data_hora_pagament.year
    else:
        ultim=current_year()
    primerCurs=Curs.objects.filter(data_inici_curs__isnull=False).order_by('data_inici_curs').first()
    ultimCurs=Curs.objects.filter(data_fi_curs__isnull=False).order_by('data_fi_curs').last()
    if primerCurs and primerCurs.data_inici_curs.year<primer:
        primer = primerCurs.data_inici_curs.year
    if ultimCurs and ultimCurs.data_fi_curs.year>ultim:
        ultim = ultimCurs.data_fi_curs.year
    return [(r,r) for r in range(primer, ultim+1)]

def current_year():
    '''
    Retorna any de l'últim pagament registrat o any actual
    '''
    ultim=QuotaPagament.objects.filter(data_hora_pagament__isnull=False).order_by('data_hora_pagament').last()
    if ultim:
        ultim = ultim.data_hora_pagament.year
    else:
        ultim = datetime.date.today().year
    return ultim

class EscollirCursForm(forms.Form):
    '''
    Permet escollir curs, tipus de quota, any i si es fa assignació automàtica
    '''
    curs_list = forms.ModelChoiceField(label=u'Curs', queryset=None, required = True,)
    tipus_quota = forms.ModelChoiceField(label=u'Tipus de quota', queryset=None, required = True,)
    year = forms.TypedChoiceField(label='Any', coerce=int, choices=year_choices, initial=current_year, required = True)
    automatic = forms.BooleanField(label=u'Assigna automàticament', required = False)

    def __init__(self, user, *args, **kwargs):
        from django.contrib.auth.models import Group
        
        super(EscollirCursForm, self).__init__(*args, **kwargs)
        #Mostra cursos amb alumnes
        self.fields['curs_list'].queryset = Curs.objects.filter(grup__alumne__isnull=False, 
                                                                grup__alumne__data_baixa__isnull=True,
                                                ).order_by('nom_curs_complert').distinct()
        di=Group.objects.filter(name='direcció')
        ad=Group.objects.filter(name='administradors')
        if (di and di[0] not in user.groups.all()) and (ad and ad[0] not in user.groups.all()):
            # Si usuari no pertany a direcció ni administradors
            # només permet tipus de quotes que coincideixen amb l'usuari
            #  Exemple:  usuari ampa --> tipus de quota "ampa" 
            self.fields['tipus_quota'].queryset = TipusQuota.objects.filter(quota__isnull=False, nom=user.username).order_by('nom').distinct()
        else:
            self.fields['tipus_quota'].queryset = TipusQuota.objects.filter(quota__isnull=False).order_by('nom').distinct()

class PagQuotesForm(forms.Form):
    '''
    Mostra les quotes assignades als alumnes seleccionats
    '''
    pkp = forms.CharField( widget=forms.HiddenInput() )
    pka = forms.CharField( widget=forms.HiddenInput() )
    cognoms = forms.CharField( widget = forms.TextInput( attrs={'readonly': True} ), required=False, )
    nom = forms.CharField( widget = forms.TextInput( attrs={'readonly': True, 'style': 'width:100px'} ), required=False, )
    grup = forms.CharField(max_length=10, widget = forms.TextInput( attrs={'readonly': True, 'style': 'width:80px'} ) )
    correu = forms.CharField( widget = forms.TextInput( attrs={'readonly': True} ), required=False, )

    quota = ModelChoiceField(
        widget=ModelSelect2Widget(
            queryset=Quota.objects.all(),
            search_fields=('importQuota__icontains', 'descripcio__icontains',),
        ),
        queryset=Quota.objects.all(),
        required=False,
        )

    estat = forms.CharField(max_length=15, widget = forms.TextInput( attrs={'readonly': True, 'style': 'width:100px'} ) )
    fracciona = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        tipus = kwargs.pop('tipus')
        super(PagQuotesForm, self).__init__(*args, **kwargs)
        self.fields['quota'].widget.queryset=Quota.objects.filter(tipus=tipus).distinct()

class EscollirTPV(forms.Form):
    '''
    Permet escollir el TPV i l'any per a la gestió de quotes
    Per defecte mostra el TPV reservat "centre", si l'usuari té permís.
    Depenent de l'usuari pot mostrar altres.
    '''
    defecte = TPV.objects.filter(nom='centre').first()
    tpv = forms.ModelChoiceField(label='TPV', queryset=None, initial=defecte, required = True,)
    year = forms.TypedChoiceField(label='Any', coerce=int, choices=year_choices, initial=current_year, required = True)
    
    def __init__(self, user, *args, **kwargs):
        from django.contrib.auth.models import Group
        
        super(EscollirTPV, self).__init__(*args, **kwargs)
        tp=Group.objects.get_or_create(name= 'tpvs' )
        if tp and tp[0] in user.groups.all():
            # Si l'usuari és del grup tpvs, només mostra el que correspon al seu nom
            #  Exemple:  usuari ampa --> TPV "ampa" 
            self.fields['tpv'].queryset = TPV.objects.filter(nom=user.username)
        else:
            self.fields['tpv'].queryset = TPV.objects.all()
