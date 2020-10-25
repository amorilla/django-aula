from django import forms
from django.conf import settings
from aula.django_select2.forms import ModelSelect2Widget
from django.forms.models import ModelChoiceField
from aula.apps.alumnes.models import Curs
from aula.apps.sortides.models import Sortida, Quota, QuotaPagament, TipusQuota

class PagamentForm(forms.Form):
    sortida = forms.CharField(widget=forms.HiddenInput())
    check = forms.BooleanField(required=True, label="")
    Ds_MerchantParameters = forms.CharField(widget=forms.HiddenInput())
    Ds_Signature = forms.CharField(widget=forms.HiddenInput())
    acceptar_condicions = forms.BooleanField(required=True)

    def __init__(self, *args, **kwargs):
        super(PagamentForm, self).__init__(*args, **kwargs)
        self.sortida = kwargs.pop('sortida', None)
        self.Ds_MerchantParameters = kwargs.pop('Ds_MerchantParameters', None)
        self.Ds_Signature = kwargs.pop('signature', None)
        self.acceptar_condicions = kwargs.pop('signature', False)

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

class EscollirCursForm(forms.Form):

    curs_list = forms.ModelChoiceField(label=u'Curs', queryset=None, required = True,)
    tipus_quota = forms.ModelChoiceField(label=u'Tipus de quota', queryset=None, required = True,)
    automatic = forms.BooleanField(label=u'Assigna automàticament', required = False)

    def __init__(self, user, *args, **kwargs):
        from django.contrib.auth.models import Group
        
        super(EscollirCursForm, self).__init__(*args, **kwargs)
        self.fields['curs_list'].queryset = Curs.objects.filter(grup__alumne__isnull=False, 
                                                                grup__alumne__data_baixa__isnull=True,
                                                ).order_by('nom_curs_complert').distinct()
        di=Group.objects.filter(name='direcció')
        ad=Group.objects.filter(name='administradors')
        if (di and di[0] not in user.groups.all()) and (ad and ad[0] not in user.groups.all()):
            self.fields['tipus_quota'].queryset = TipusQuota.objects.exclude(nom='uf').exclude(nom='taxcurs').filter(quota__isnull=False, nom=user.groups.all()[0].name).order_by('nom').distinct()
        else:
            self.fields['tipus_quota'].queryset = TipusQuota.objects.exclude(nom='uf').exclude(nom='taxcurs').filter(quota__isnull=False).order_by('nom').distinct()

class PagQuotesForm(forms.Form):
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


import datetime

def year_choices():
    primer=QuotaPagament.objects.filter(pagament_realitzat=True).order_by('data_hora_pagament').first()
    if primer:
        primer = primer.data_hora_pagament.year
        return [(r,r) for r in range(primer, datetime.date.today().year+1)]
    else:
        return [(current_year(),current_year())]

def current_year():
    return datetime.date.today().year

class EscollirAny(forms.Form):
    from aula.apps.sortides.models import Comerç
    
    defecte = Comerç.objects.all().order_by('id').first()
    tpv = forms.ModelChoiceField(label='TPV', queryset=None, initial=defecte, required = True,)
    year = forms.TypedChoiceField(label='Any', coerce=int, choices=year_choices, initial=current_year, required = True)
    
    def __init__(self, user, *args, **kwargs):
        from aula.apps.sortides.models import Comerç
        from django.contrib.auth.models import Group
        
        super(EscollirAny, self).__init__(*args, **kwargs)
        di=Group.objects.filter(name='direcció')
        ad=Group.objects.filter(name='administradors')
        if (di and di[0] not in user.groups.all()) and (ad and ad[0] not in user.groups.all()):
            self.fields['tpv'].queryset = Comerç.objects.filter(descripcio=user.groups.all()[0].name)
        else:
            self.fields['tpv'].queryset = Comerç.objects.all().order_by('id')