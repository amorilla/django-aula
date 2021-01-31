from django import forms
from captcha.fields import CaptchaField
from aula.apps.matricula.models import Peticio, Dades
from aula.apps.sortides.models import QuotaPagament
from aula.apps.alumnes.models import Curs
from aula.apps.extPreinscripcio.models import Preinscripcio
from aula.utils.widgets import DateTextImput

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

class AcceptaCond(forms.ModelForm):
    
    def __init__(self, user, *args, **kwargs):
        super(AcceptaCond, self).__init__(*args, **kwargs)
        self.fields['acceptar_condicions'].required=True
        self.fields['acceptar_condicions'].label=""
        self.fields['alumne_correu'].required=True
        self.fields['alumne_correu'].label="Correu per notificacions"
        self.fields['alumne_correu'].initial=user.alumne.correu
    
    class Meta:
        model=Dades
        fields = ['alumne_correu', 'acceptar_condicions',]

class MatriculaForm(forms.ModelForm):
    
    class Meta:
        model = Dades
        fields = ['nom','cognoms','acceptar_condicions','files',]
