from django import forms
from captcha.fields import CaptchaField
from aula.apps.matricula.models import Peticio, Dades
from aula.apps.sortides.models import Quota, TipusQuota, QuotaPagament
from aula.apps.alumnes.models import Curs, Alumne
from aula.apps.extPreinscripcio.models import Preinscripcio
from aula.utils.widgets import DateTextImput
from aula.django_select2.forms import ModelSelect2Widget
from django.forms.models import ModelChoiceField

def obteCurs(preinscripcio):
    if not preinscripcio:
        return Curs.objects.get(nivell__nom_nivell='ESO', nom_curs=1)
    codiestudis=preinscripcio.codiestudis
    curs=preinscripcio.curs
    if codiestudis=='ESO LOE':
        c=Curs.objects.filter(nivell__nom_nivell='ESO', nom_curs=curs)
        if c:
            return c[0]
    return Curs.objects.get(nivell__nom_nivell=codiestudis, nom_curs=curs)

class peticioForm(forms.ModelForm):
    '''
    Formulari petició de Matrícula
    Demana un captcha per evitar accesos automàtics, configurat al settings.
    '''
    
    captcha = CaptchaField(label="")

    class Meta:
        model = Peticio
        fields = ['idAlumne','tipusIdent','email']#,'curs']
        
    def __init__(self, *args, **kwargs):
        super(peticioForm, self).__init__(*args, **kwargs)
        #self.fields['curs'].queryset = Curs.objects.filter(nivell__matricula_oberta=True).order_by('nom_curs_complert')
    
    def clean(self):
        cleaned_data = super(peticioForm, self).clean()
        idAlumne = cleaned_data.get('idAlumne').upper()
        tipus = cleaned_data.get('tipusIdent')
        if tipus=='R':
            # Comprova per RALC
            p=Preinscripcio.objects.filter(ralc=idAlumne)
        else:
            # Comprova per DNI
            p=Preinscripcio.objects.filter(identificador=idAlumne)
        if not p:
            raise forms.ValidationError("Identificador RALC o DNI erròni")
        self.instance.curs = obteCurs(p[0])
        cleaned_data['curs'] = self.instance.curs
        self.instance.idAlumne = idAlumne
        cleaned_data['idAlumne'] = self.instance.idAlumne
        return cleaned_data  

class DadesForm1(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(DadesForm1, self).__init__(*args, **kwargs)
        self.fields['data_naixement'].widget=DateTextImput()
        
    class Meta:
        model=Dades
        fields = ['nom','cognoms','centre_de_procedencia','data_naixement','alumne_correu','adreca','localitat','cp',]

class DadesForm2(forms.ModelForm):
    
    class Meta:
        model=Dades
        fields = ['rp1_nom','rp1_telefon1','rp1_correu','rp2_nom','rp2_telefon1','rp2_correu',]

class DadesForm2b(forms.ModelForm):
    
    llistaufs = forms.CharField(widget=forms.Textarea, required=False)
    
    class Meta:
        model=Dades
        fields = ['curs_complet', 'quantitat_ufs', 'llistaufs', 'bonificacio', ]

    def __init__(self, *args, **kwargs):
        super(DadesForm2b, self).__init__(*args, **kwargs)
        idpeticio = kwargs['initial'].pop('peticio')
        p=Peticio.objects.get(pk=idpeticio)
        taxes=p.curs.nivell.taxes
        if not taxes:
            self.fields['bonificacio'].help_text='No s\'apliquen taxes en aquest curs'
            self.fields['bonificacio'].disabled=True
        pag=QuotaPagament.objects.filter(alumne=p.alumne, quota__any=p.any, quota__tipus=taxes, pagament_realitzat=True)
        if pag:
            self.fields['curs_complet'].disabled=True
            self.fields['quantitat_ufs'].disabled=True
            self.fields['llistaufs'].disabled=True
            self.fields['bonificacio'].disabled=True
        
    def clean(self):
        cleaned_data = super(DadesForm2b, self).clean()
        complet = cleaned_data.get('curs_complet')
        ufs = cleaned_data.get('quantitat_ufs')
        llista = cleaned_data.get('llistaufs')
        if not complet and ufs<=0:
            raise forms.ValidationError("Si no és curs complet, la quantitat de UFs és obligatòria")
        if complet and ufs!=0:
            raise forms.ValidationError("Si curs complet no s'ha d'introduir quantitat de UFs")
        if ufs>0 and not llista:
            raise forms.ValidationError("Indica les UFs a on vols matricular-te")
        return cleaned_data

class DadesForm3(forms.ModelForm):
    
    quotaMat=forms.CharField(label="Quota Matrícula:", widget = forms.TextInput( attrs={'readonly': True} ), required=False, )
    importTaxes=forms.CharField(label="Import de les taxes:", widget = forms.TextInput( attrs={'readonly': True} ), required=False, )

    def __init__(self, *args, **kwargs):
        super(DadesForm3, self).__init__(*args, **kwargs)
        self.fields['acceptar_condicions'].required=True
        self.fields['files'].help_text="És necessari el document de la titulació aportada (ESO, BAT, ...) i/o compliment de les bonificacions.\nEnvia tot en un zip."
        idpeticio = kwargs['initial'].pop('peticio')
        importTaxes = kwargs['initial'].pop('importTaxes')
        p=Peticio.objects.get(pk=idpeticio)
        taxes=p.curs.nivell.taxes
        pag=QuotaPagament.objects.filter(alumne=p.alumne, quota__any=p.any, quota__tipus=taxes, pagament_realitzat=True)
        if not taxes or pag or importTaxes==0:
            self.fields['fracciona_taxes'].disabled=True
    
    class Meta:
        model=Dades
        fields = ['quotaMat', 'importTaxes', 'fracciona_taxes', 'files', 'acceptar_condicions',]

class MatriculaForm(forms.ModelForm):
    
    class Meta:
        model = Dades
        fields = ['nom','cognoms','acceptar_condicions','files',]

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
    primer=QuotaPagament.objects.filter(pagament_realitzat=True).order_by('data_hora_pagament').first().data_hora_pagament.year
    return [(r,r) for r in range(primer, datetime.date.today().year+1)]

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
