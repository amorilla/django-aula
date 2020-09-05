from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.views.generic.edit import UpdateView
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
import django.utils.timezone
from dateutil.relativedelta import relativedelta
import random
from formtools.wizard.views import SessionWizardView
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect
from django.conf import settings
from aula.utils.decorators import group_required
from aula.apps.matricula.forms import peticioForm, DadesForm1, DadesForm2, DadesForm2b, DadesForm3, MatriculaForm, EscollirCursForm, PagQuotesForm, EscollirAny
from aula.apps.matricula.models import Peticio, Dades
from aula.apps.sortides.models import QuotaPagament, Quota
from aula.apps.alumnes.models import Alumne, Curs, Nivell
from aula.apps.extPreinscripcio.models import Preinscripcio
from aula.apps.extSaga.models import ParametreSaga
from aula.apps.extUntis.sincronitzaUntis import creaGrup
from aula.apps.usuaris.models import OneTimePasswd

def get_url_alumne(usuari):
    '''
    Si l'usuari és un alumne i té una petició de matrícula acceptada que encara
    no ha omplert les dades retorna la url per omplir la informació
    en altre cas retorna None
    '''
    
    try:
        if usuari.alumne:
            p=Peticio.objects.filter(alumne=usuari.alumne, any=django.utils.timezone.now().year, estat='A')
            if p:
                p=p[0]
                if not p.dades:
                    return reverse_lazy('matricula:relacio_families__matricula__dades')
    except Exception:
        return None
    return None

def autoRalc(ident):
    '''
    Calcula Ralc per a alumnes que no tenen.
    ident identificador de l'alumne, normalment DNI
    Utilitza el paràmetre autoRalc de paràmetres Saga, crea un identificador 
    format per parametre + ident
    Retorna el ralc calculat 
    '''
    autoRalc, _ = ParametreSaga.objects.get_or_create( nom_parametre = 'autoRalc' )
    if bool(autoRalc.valor_parametre):
        ralc= autoRalc.valor_parametre + ident[-9:]
        return ralc
    return ident

def alumneExisteix(idalum):
    '''
    Retorna objecte Alumne que correspon a ralc=idalum
    Retorna None si no existeix
    '''
    ralc=idalum
    al=Alumne.objects.filter(ralc=ralc)
    if al:
        return al[0]
    ralc=autoRalc(idalum)
    al=Alumne.objects.filter(ralc=ralc)
    if al:
        return al[0]
    return None

def mailPeticio(estat, idalum, email, alumne=None):
    '''
    Envia email segons l'estat de la petició de matrícula
    estat de la petició ('P', 'R', 'D', 'A' o 'F')
    idalum identificador d'alumne
    email  adreça email destinataria
    alumne objecte Alumne si matrícula completada o None
    '''
    
    if estat=='A':
        #preparo el codi a la bd:
        clau = str( random.randint( 100000, 999999) ) + str( random.randint( 100000, 999999) )
        OneTimePasswd.objects.create(usuari = alumne.get_user_associat(), clau = clau)
        
        #envio missatge:
        urlDjangoAula = settings.URL_DJANGO_AULA
        username=alumne.get_user_associat().username
        url = "{0}/usuaris/recoverPasswd/{1}/{2}".format( urlDjangoAula, username, clau )
    else:
        username=''
        url=''
    
    if estat=='F':
        username=alumne.get_user_associat().username
    
    assumpte = {
        'P': u"Petició de matrícula rebuda - {0}".format(settings.NOM_CENTRE ),
        'R': u"Petició de matrícula incorrecte - {0}".format(settings.NOM_CENTRE ),
        'D': u"Petició de matrícula duplicada - {0}".format(settings.NOM_CENTRE ),
        'A': u"Tràmits de matrícula - {0}".format(settings.NOM_CENTRE ),
        'F': u"Matrícula completada - {0}".format(settings.NOM_CENTRE ),
        }
    cosmissatge={
        'P': u"Hem rebut la seva petició de matrícula, un cop verificada rebrà un email amb noves instruccions.",
        'R': u"La seva petició de matrícula no correspon a cap preinscripció. No és possible fer el tràmit.",
        'D': u"La seva petició de matrícula és una duplicitat, ja té una matrícula anterior acceptada.",
        'A': u"\n".join(
            [u"El motiu d'aquest correu és el de donar-vos les instruccions per a realitzar la matrícula al nostre centre.",
            u"El vostre usuari és {0} i el primer pas es obtenir la contrasenya:".format(username),
            u" * Entreu a {0} on podeu escollir la vostra contrasenya.".format(url),
            u" * Una vegada accediu a l'aplicació podreu continuar la matrícula.",
            u"",
            u"Sempre podreu accedir a l'aplicació {0} amb el vostre usuari {1} i la contrasenya escollida".format(settings.URL_DJANGO_AULA, username ),]
            ),
        'F': u"La matrícula de l'alumne {0} ha finalitzat correctament.\n".format(str(alumne)) + \
            "Sempre podreu accedir a l'aplicació {0} amb el vostre usuari {1}\n".format(settings.URL_DJANGO_AULA, username) + \
            "Puja una fotografía tipus carnet des de l'opció de paràmetres.",
        }
    missatge = [u"Aquest missatge ha estat enviat per un sistema automàtic. No respongui a aquest e-mail, el missatge no serà llegit per ningú.",
                u"",
                u"Benvolgut/da,",
                u"",
                cosmissatge.get(estat),
                u"",
                u"Cordialment,",
                u"",
                settings.NOM_CENTRE,
                ]                        
    fromuser = settings.DEFAULT_FROM_EMAIL
    if settings.DEBUG:
        print (u'Enviant comunicació sobre la petició a {0}'.format( idalum ))
    try:
        send_mail(assumpte.get(estat), 
                  u'\n'.join( missatge ), 
                  fromuser,
                  (email,), 
                  fail_silently=False)
    except Exception as e:
        print("Error send_mail petició "+str(e))

def creaAlumne(idalum, tipus, curs, email):
    '''
    Crea l'alumne, assigna grup sense lletra. Activa l'usuari per a poder fer Login.
    idalum identificador d'alumne
    tipus 'R' Ralc o 'D' DNI
    curs  objecte Curs de l'alumne
    email  adreça email destinataria
    Retorna objecte Alumne
    '''
    
    al=alumneExisteix(idalum)
    if al:
        return al
    al=Alumne()
    if tipus=='D':
        al.ralc=autoRalc(idalum)
    else:
        al.ralc=idalum
    grup , _ = creaGrup(curs.nivell.nom_nivell,curs.nom_curs,'-',None,None)
    al.grup=grup
    al.correu_tutors=email
    al.correu_relacio_familia_pare=email
    al.tutors_volen_rebre_correu=True
    al.save()
    al.user_associat.is_active=True
    al.user_associat.save()
    return al

def creaPagament(alumne, quota, fracciona=False):
    '''
    Crea pagament de la quota per a l'alumne
    '''
    
    p=QuotaPagament.objects.filter(alumne=alumne, quota=quota)
    if not p and quota:
        if fracciona and quota.importQuota!=0:
            import1=round(float(quota.importQuota)/2.00,2)
            import2=float(quota.importQuota)-import1
            p=QuotaPagament(alumne=alumne, quota=quota, fracciona=True, importParcial=import1, dataLimit=quota.dataLimit)
            p.save()
            p=QuotaPagament(alumne=alumne, quota=quota, fracciona=True, importParcial=import2, 
                            dataLimit=quota.dataLimit + relativedelta(months=+1))
            p.save()
        else:
            p=QuotaPagament(alumne=alumne, quota=quota)
            p.save()

def gestionaPag(peticio, importTaxes):
    taxes=peticio.curs.nivell.taxes
    quotamat=peticio.quota
    if taxes and importTaxes>0:
        quotatax=Quota.objects.filter(importQuota=importTaxes, any=peticio.any, tipus=taxes)
        if quotatax:
            quotatax=quotatax[0]
        else:
            quotatax=None
    else:
        quotatax=None
    fracciona=peticio.dades.fracciona_taxes
    # Quota matrícula
    pag=QuotaPagament.objects.filter(alumne=peticio.alumne, quota__any=peticio.any, 
                                     quota__tipus__nom=settings.CUSTOM_TIPUS_QUOTA_MATRICULA)
    if pag:
        if (pag[0].quota!=quotamat and not pag.filter(pagament_realitzat=True)):
            # esborra antiga, crea nova
            pag.delete()
            creaPagament(peticio.alumne, quotamat)
    else:
        creaPagament(peticio.alumne, quotamat)
    
    # Quota taxes
    pag=QuotaPagament.objects.filter(alumne=peticio.alumne, quota__any=peticio.any, 
                                     quota__tipus=taxes)
    if pag:
        if (pag[0].quota!=quotatax and not pag.filter(pagament_realitzat=True)) or \
            (pag[0].quota==quotatax and not pag.filter(pagament_realitzat=True) and \
             pag[0].fracciona!=fracciona):        
            # esborra antiga, crea nova
            pag.delete()
            creaPagament(peticio.alumne, quotatax, fracciona)
    else:
        creaPagament(peticio.alumne, quotatax, fracciona)

def peticio(request):
    '''
    View per a fer la petició de matrícula
    Crea Peticio pendent (tipus 'P') amb les dades i envia email de confirmació de recepció.
    Si es una petició repetida, acceptada prèviament, la marca com duplicada 'D'.
    '''
    
    if not Nivell.objects.filter(nom_nivell='ESO', matricula_oberta=True):
        infos=[]
        infos.append('El procés de matrícula online per l\'ESO ha finalitzat.')
        return render(
                    request,
                    'resultat.html', 
                    {'msgs': {'errors': [], 'warnings': [], 'infos': infos} },
                 )
    
    if request.method == 'POST':
        form = peticioForm(request.POST)
        if form.is_valid():
            infos=[]
            errors=[]
            novaPeticio=form.save()
            toaddress = novaPeticio.email
            idalum = novaPeticio.idAlumne
            ralc=None
            dni=None
            if novaPeticio.tipusIdent=='R':
                # Comprova per RALC
                p=Preinscripcio.objects.filter(ralc=idalum, correu=toaddress)
                if p:
                    estat='A'
                    dni=p[0].identificador if p[0].identificador else None
                else:
                    #  No existeix amb aquest RALC
                    estat='P'
                ralc=idalum
            else:
                # Comprova per DNI
                p=Preinscripcio.objects.filter(identificador=idalum, correu=toaddress)
                if p:
                    estat='A'
                    if not p[0].ralc:
                        # si no té RALC es crea un automàtic
                        ralc=autoRalc(idalum)
                    else:
                        ralc=p[0].ralc
                else:
                    #  No existeix amb aquest DNI
                    estat='P'
                dni=idalum

            if ralc:
                pralc=Peticio.objects.filter(idAlumne=ralc, tipusIdent='R', any=novaPeticio.any, estat__in=('A','F',)).exclude(pk=novaPeticio.pk)
            else:
                pralc=None
            if dni:
                pdni=Peticio.objects.filter(idAlumne=dni, tipusIdent='D', any=novaPeticio.any, estat__in=('A','F',)).exclude(pk=novaPeticio.pk)
            else:
                pdni=None
            if pralc or pdni:
                # Si ja té una matrícula iniciada, marca la petició com duplicada.
                estat='D'
                novaPeticio.estat='D'
                novaPeticio.save()
            
            if estat=='A':
                # Canvia les peticions pendents o rebutjades a duplicades
                if ralc:
                    Peticio.objects.filter(idAlumne=ralc, tipusIdent='R', any=novaPeticio.any, estat__in=('P','R',)).exclude(pk=novaPeticio.pk).update(estat='D')
                if dni:
                    Peticio.objects.filter(idAlumne=dni, tipusIdent='D', any=novaPeticio.any, estat__in=('P','R',)).exclude(pk=novaPeticio.pk).update(estat='D')
                
                alumne=creaAlumne(ralc, 'R', novaPeticio.curs, toaddress)
                quotacurs=Quota.objects.filter(curs=novaPeticio.curs, any=novaPeticio.any, tipus__nom=settings.CUSTOM_TIPUS_QUOTA_MATRICULA)
                if quotacurs:
                    quotacurs=quotacurs[0]
                    creaPagament(alumne, quotacurs)
                    novaPeticio.quota=quotacurs
                    novaPeticio.estat='A'
                else:
                    if settings.CUSTOM_TIPUS_QUOTA_MATRICULA:
                        novaPeticio.estat='P'
                    else:
                        novaPeticio.estat='A'
                novaPeticio.alumne=alumne
                novaPeticio.save()
                mailPeticio(novaPeticio.estat, idalum, toaddress, alumne)
            else:
                mailPeticio(estat, idalum, toaddress)
            
            '''
            if estat=='D':
                infos.append('Petició duplicada, ja existeix una matrícula acceptada per a aquest alumne.')
            else:
            '''
            infos.append('Petició rebuda, un cop verificada rebrà un email amb noves instruccions.')
            
            return render(
                        request,
                        'resultat.html', 
                        {'msgs': {'errors': errors, 'warnings': [], 'infos': infos} },
                     )
            
    else:
        form = peticioForm()
    return render(request, 'peticio.html', {'form': form, 'titol_formulari': 'Petició de matrícula'})
    
class PeticioDetail(LoginRequiredMixin, UpdateView):
    '''
    View per editar una Peticio
    Al finalitzar mostra la següent
    '''
    
    model = Peticio
    template_name='peticio_form.html'
    fields = ['idAlumne', 'tipusIdent', 'email', 'curs', 'estat', 'quota']
    
    def get_success_url(self):
        pk=self.object.pk
        queryset = Peticio.objects.filter(pk__gt=pk, estat='P', any=django.utils.timezone.now().year)
        if queryset:
            pk=queryset[0].pk
            return reverse_lazy("matricula:gestio__peticions__pendents", kwargs={"pk": pk})
        else:
            queryset = Peticio.objects.filter(estat='P', any=django.utils.timezone.now().year)
            if queryset:
                pk=queryset[0].pk
                return reverse_lazy("matricula:gestio__peticions__pendents", kwargs={"pk": pk})
            return reverse_lazy('matricula:gestio__peticions__pendents')

    def get_form(self, form_class=None):
        form = super(PeticioDetail, self).get_form(form_class)
        form.fields['curs'].queryset = Curs.objects.filter(nivell__matricula_oberta=True).order_by('nom_curs_complert')
        form.fields['quota'].queryset = Quota.objects.filter(any=django.utils.timezone.now().year, tipus__nom=settings.CUSTOM_TIPUS_QUOTA_MATRICULA)
        form.fields['quota'].required = True if settings.CUSTOM_TIPUS_QUOTA_MATRICULA else False
        form.fields['estat'].choices = [('A','Acceptada'), ('R','Rebutjada'),]
        return form

    def form_valid(self, form):
        '''
        Envia el email amb la resposta a la petició
            si estat R Rebutjada
            si estat A Acceptada
                Crea un Alumne per a la petició
            si estat F Finalitzada
        '''
        
        self.object = form.save()
        estat=self.object.estat
        idalum=self.object.idAlumne
        email=self.object.email
        if estat=='R':
            mailPeticio(estat, idalum, email)
        if estat=='A':
            # Canvia les peticions pendents o rebutjades a duplicades
            Peticio.objects.filter(idAlumne=idalum, tipusIdent=self.object.tipusIdent, email=email, any=self.object.any, estat__in=('P','R',)).update(estat='D')
            alumne=creaAlumne(idalum, self.object.tipusIdent, self.object.curs, email)
            creaPagament(alumne, self.object.quota)
            self.object.alumne=alumne
            self.object.save()
            mailPeticio(estat, idalum, email, alumne)
        return super().form_valid(form)

@login_required
@group_required(['direcció','administradors'])
def PeticiobyId(request, pk=None):
    return PeticioDetail.as_view()(request, pk=pk)

@login_required
@group_required(['direcció','administradors'])
def PeticioVerifica(request):
    '''
    View que verifica les peticions
    Mostra una petició pendent de verificació
    '''
    
    queryset = Peticio.objects.filter(estat='P', any=django.utils.timezone.now().year)
    if queryset:
        pk=queryset[0].pk
        return PeticioDetail.as_view()(request, pk=pk)
    else:
        infos=[]
        infos.append('Sense peticions pendents de verificació')
        return render(
                    request,
                    'resultat.html', 
                    {'msgs': {'errors': [], 'warnings': [], 'infos': infos} },
                 )

class DadesView(LoginRequiredMixin, SessionWizardView):
    form_list = [DadesForm1, DadesForm2, DadesForm2b, DadesForm3]
    template_name = 'dades_form.html'
    file_storage = FileSystemStorage(location=settings.PRIVATE_STORAGE_ROOT)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titol'] = self.kwargs.get('titol', None)
        pagid = self.kwargs.get('pagid', None)
        context['pagament'] = QuotaPagament.objects.get(pk=pagid) if bool(pagid) else None
        return context

    def get_form_initial(self, step):
        if step == '2':
            p=Peticio.objects.get(alumne=self.request.user.alumne, estat='A', any=django.utils.timezone.now().year)
            dictf2=self.initial_dict.get(step, {})
            dictf2.update({'peticio': p.id})
            return dictf2
        if step == '3': 
            step2data = self.get_cleaned_data_for_step('2')
            if step2data:
                complet = step2data.get('curs_complet', False)
                ufs = step2data.get('quantitat_ufs', 0)
                bonif = step2data.get('bonificacio', '0')
                al=self.request.user.alumne
                p=Peticio.objects.get(alumne=al, estat='A', any=django.utils.timezone.now().year)
                taxes=p.curs.nivell.taxes
                tcomplet=Quota.objects.filter(any=django.utils.timezone.now().year, tipus__nom='taxcurs')
                tuf=Quota.objects.filter(any=django.utils.timezone.now().year, tipus__nom='uf')
                quotamat=Quota.objects.filter(curs=p.curs, any=p.any, tipus__nom=settings.CUSTOM_TIPUS_QUOTA_MATRICULA)
                total=0
                if complet and taxes and tcomplet:
                    total=tcomplet[0].importQuota
                else:
                    if taxes and tuf and ufs>0:
                        total=ufs*tuf[0].importQuota
                if bonif=='5':
                    total=total/2
                if bonif=='1':
                    total=0
                dictf3=self.initial_dict.get(step, {})
                dictf3['importTaxes']=total
                dictf3['quotaMat']=quotamat[0].importQuota
                dictf3.update({'peticio': p.id})
                return dictf3
        return self.initial_dict.get(step, {})
   
    def done(self, form_list, **kwargs):
        from decimal import Decimal
        
        data=self.get_all_cleaned_data()
        if 'pk' in kwargs:
            iddata = kwargs['pk']
            item = Dades.objects.get(pk=iddata)
        else:
            item = Dades()
        for field, value in iter(data.items()):
            setattr(item, field, value)

        item.save()
        al=self.request.user.alumne
        p=Peticio.objects.get(alumne=al, estat='A', any=django.utils.timezone.now().year)
        p.dades=item
        p.save()
        al.nom=item.nom
        al.cognoms=item.cognoms
        al.save()
        importTaxes=Decimal(data.get('importTaxes',''))
        infos=[]
        url_next=[]
        if p.quota and "quota" in self.request.POST:
            # redirect pagament online
            pagament=QuotaPagament.objects.filter(alumne=p.alumne, quota=p.quota).order_by('dataLimit')[0]
            return (HttpResponseRedirect(reverse_lazy('sortides__sortides__pago_on_line',
                                        kwargs={'pk': pagament.id})+'?next=/')) #'?next='+str(self.request.get_full_path())))
        else:
            gestionaPag(p, importTaxes)
            from django.utils.html import format_html
            
            url=format_html("<a href='{}'>{}</a>",
                      reverse_lazy('relacio_families__informe__el_meu_informe'),
                      'Activitats/Pagaments')            
            infos.append('Dades completades, una vegada siguin revisades per secretaria rebrà un missatge. '\
                         'Gestioni els pagaments des de l\'apartat '+url)
            
            '''
            pagament=QuotaPagament.objects.filter(alumne=p.alumne, quota=p.quota).order_by('dataLimit')
            if pagament and not pagament[0].pagamentFet:
                infos.append('Dades completades, una vegada siguin revisades per secretaria rebrà un missatge. Falta el pagament de la quota.')
            else:
                infos.append('Dades completades, una vegada siguin revisades per secretaria rebrà un missatge.')
            '''
        return render(
                    self.request,
                    'resultat.html', 
                    {'msgs': {'errors': [], 'warnings': [], 'infos': infos, 'url_next':url_next} },
                 )

def dadesAntigues(alumne):
    d=Dades()
    p=Preinscripcio.objects.filter(ralc=alumne.ralc)
    if p:
        p=p[0]
        d.nom=p.nom
        d.cognoms=p.cognoms
        d.centre_de_procedencia=p.centreprocedencia
        d.data_naixement=p.naixement
        d.alumne_correu=p.correu
        d.adreca=p.adreça
        d.localitat=p.localitat
        d.cp=p.cp
        d.rp1_nom=p.nomtut1+" "+p.cognomstut1 if p.nomtut1 and p.cognomstut1 else None
        d.rp1_telefon1=p.telefon
        d.rp1_correu=p.correu
        d.rp2_nom=p.nomtut2+" "+p.cognomstut2 if p.nomtut2 and p.cognomstut2 else None
    else:
        d.nom=alumne.nom
        d.cognoms=alumne.cognoms
        d.centre_de_procedencia=alumne.centre_de_procedencia
        d.data_naixement=alumne.data_neixement
        d.alumne_correu=alumne.correu
        d.adreca=alumne.adreca
        d.localitat=alumne.localitat
        d.cp=alumne.cp
        d.rp1_nom=alumne.rp1_nom
        d.rp1_telefon1=alumne.rp1_mobil if alumne.rp1_mobil else alumne.rp1_telefon
        d.rp1_correu=alumne.rp1_correu
        d.rp2_nom=alumne.rp2_nom
        d.rp2_telefon1=alumne.rp2_mobil if alumne.rp2_mobil else alumne.rp2_telefon
        d.rp2_correu=alumne.rp2_correu
    return d

def updateAlumne(alumne, dades):
    alumne.nom=dades.nom
    alumne.cognoms=dades.cognoms
    alumne.centre_de_procedencia=dades.centre_de_procedencia if dades.centre_de_procedencia else ''
    alumne.data_neixement=dades.data_naixement
    alumne.correu=dades.alumne_correu
    alumne.adreca=dades.adreca
    alumne.localitat=dades.localitat
    alumne.cp=dades.cp
    alumne.rp1_nom=dades.rp1_nom
    alumne.rp1_telefon=dades.rp1_telefon1
    alumne.rp1_correu=dades.rp1_correu
    alumne.rp2_nom=dades.rp2_nom if dades.rp2_nom else ''
    alumne.rp2_telefon=dades.rp2_telefon1 if dades.rp2_telefon1 else ''
    alumne.rp2_correu=dades.rp2_correu if dades.rp2_correu else ''
    alumne.correu_relacio_familia_pare = alumne.rp1_correu
    alumne.correu_relacio_familia_mare = alumne.rp2_correu
    alumne.save()

@login_required
def OmpleDades(request, pk=None):
    from django.utils.datetime_safe import  date, datetime

    user=request.user
    infos=[]
    try:
        if user.alumne:
            p=Peticio.objects.filter(alumne=user.alumne, any=django.utils.timezone.now().year).exclude(estat='D')
            if p:
                p=p[0]
                if p.estat=='A':
                    data = datetime.strptime('2020-09-08', r"%Y-%m-%d")
                    if django.utils.timezone.now()>=data:
                        infos.append('El període de matrícula ha finalitzat.')
                        return render(
                            request,
                            'resultat.html', 
                            {'msgs': {'errors': [], 'warnings': [], 'infos': infos} },
                            )
                    pagament=QuotaPagament.objects.filter(alumne=p.alumne, quota=p.quota).order_by('dataLimit')
                    if pagament:
                        pagid=pagament[0].pk
                    else:
                        pagid=''
                    
                    if p.dades:
                        item=p.dades
                    else:
                        item=dadesAntigues(p.alumne)
                        item.rp1_correu=p.email
                    nomAlumne=(item.nom+" "+item.cognoms) if item.nom and item.cognoms else p.idAlumne
                    torn=Preinscripcio.objects.get(ralc=p.alumne.ralc).torn
                    titol="Dades de matrícula de "+nomAlumne+" a "+p.curs.nom_curs_complert+"("+torn+")"
                    #get the initial data to include in the form
                    fields0 = ['nom','cognoms','centre_de_procedencia','data_naixement','alumne_correu','adreca','localitat','cp',]
                    fields1 = ['rp1_nom','rp1_telefon1','rp1_correu','rp2_nom','rp2_telefon1','rp2_correu',]
                    fields2 = ['curs_complet', 'quantitat_ufs', 'bonificacio', 'llistaufs',]
                    fields3 = ['fracciona_taxes', 'acceptar_condicions','files',]
                    initial = {'0': dict([(f,getattr(item,f)) for f in fields0]),
                               '1': dict([(f,getattr(item,f)) for f in fields1]),
                               '2': dict([(f,getattr(item,f)) for f in fields2]),
                               '3': dict([(f,getattr(item,f)) for f in fields3]),
                    }
                    initial['3']['acceptar_condicions']=False
                    if item.pk:
                        return DadesView.as_view(initial_dict=initial)(request, pk=item.pk, titol=titol, pagid=pagid)
                    else:
                        return DadesView.as_view(initial_dict=initial)(request, titol=titol, pagid=pagid)
                else:
                    if p.estat=='F':
                        infos.append('Matrícula finalitzada. No fan falta més dades.')
                    else:
                        infos.append('Petició pendent de verificació.')
            else:
                infos.append('Sense dades necessàries')
        else:
            infos.append('Sense dades necessàries')
    except Exception as e:
        print(str(e))
        infos.append('Error a l\'accedir a les dades de matrícula: '+str(e))
        
    return render(
                request,
                'resultat.html', 
                {'msgs': {'errors': [], 'warnings': [], 'infos': infos} },
             )

class DadesShow(LoginRequiredMixin, DetailView):
    model = Dades
    template_name='dades_detail.html'
    fields = '__all__'

@login_required
@group_required(['direcció','administradors'])
def DadesbyId(request, pk=None):
    return DadesShow.as_view()(request, pk=pk)

@login_required
@group_required(['direcció','administradors'])
def changeEstat(request, pk):
    p=Peticio.objects.get(pk=pk)
    p.estat='F'
    p.save()
    updateAlumne(p.alumne, p.dades)
    mailPeticio(p.estat, p.idAlumne, p.email, p.alumne)
    return HttpResponseRedirect(reverse_lazy('matricula:gestio__confirma__matricula'))

@login_required
def condicions(request):
    f = open(settings.CONDICIONS_MATRICULA, 'r', encoding='UTF-8')
    file_content = f.read()
    f.close()
    file_content = "<br />".join(file_content.split("\n"))
    return render(
                request,
                'file_form.html', 
                {'dat': file_content },
             )

class MatriculesView(LoginRequiredMixin, ListView):
    model = Dades
    template_name='dades_list.html'
    form_class = MatriculaForm
    #paginate_by = 3
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titol'] = 'Matrícules pendents de confirmació'
        return context
    
    def get_queryset(self):
        return Dades.objects.filter(peticio__curs__nivell__matricula_oberta=True, peticio__any=django.utils.timezone.now().year, peticio__estat='A', acceptar_condicions=True).order_by('peticio__curs__nom_curs_complert', 'cognoms', 'nom')
    
@login_required
@group_required(['direcció','administradors'])
def LlistaMat(request):
    return MatriculesView.as_view()(request)

class MatriculesList(LoginRequiredMixin, ListView):
    model = Dades
    template_name='dades_list.html'
    form_class = MatriculaForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titol'] = 'Matrícules'
        return context
        
    def get_queryset(self):
        return Dades.objects.filter(peticio__curs__nivell__matricula_oberta=True, peticio__any=django.utils.timezone.now().year).order_by('peticio__curs__nom_curs_complert', 'cognoms', 'nom')

@login_required
@group_required(['direcció','administradors'])
def LlistaMatFinals(request):
    return MatriculesList.as_view()(request)

@login_required
@group_required(['direcció','administradors'])
def assignaQuotes(request):
    if request.method == 'POST':
        form = EscollirCursForm(request.POST)
        if form.is_valid():
            curs=form.cleaned_data['curs_list']
            tipus=form.cleaned_data['tipus_quota']
            return HttpResponseRedirect(reverse_lazy("matricula:gestio__quotes__assigna", 
                                                     kwargs={"curs": curs.id, "tipus": tipus.id}))
    else:
        form = EscollirCursForm()
    return render(
                request,
                'form.html', 
                {'form': form, 
                 },
                )

def get_QuotaPagament(alumne, tipus, nany=None):
    if not nany:
        nany=django.utils.timezone.now().year
    return QuotaPagament.objects.filter(alumne=alumne, quota__tipus=tipus, quota__any=nany)

@login_required
@group_required(['direcció','administradors'])
def quotesCurs( request, curs, tipus ):
    from django.forms import formset_factory

    if request.method == "POST":
        formsetQuotes = formset_factory(PagQuotesForm) 
        formset = formsetQuotes(request.POST, form_kwargs={'tipus': tipus}) 
        if formset.is_valid():
            fraccions_esborrades=()
            for form in formset:
                pg = form.cleaned_data
                quota = pg.get('quota')
                pkp = pg.get('pkp')
                pka = pg.get('pka')
                if pkp!='None' and int(pkp) in fraccions_esborrades:
                    continue
                pagament=QuotaPagament.objects.get(pk=pkp) if pkp!='None' else None
                a=Alumne.objects.get(pk=pka)
                if quota:
                    fracciona = pg.get('fracciona') and quota.importQuota>0
                    if pagament:
                        fet_act=pagament.pagamentFet
                        canviFracc=not pagament.fracciona and fracciona and not fet_act
                        canviQuota=pagament.quota!=quota and not fet_act and not pagament.fracciona
                        crea=canviQuota or canviFracc
                    else:
                        canviQuota=False
                        canviFracc=False
                        crea=True

                    if canviQuota or canviFracc:
                        QuotaPagament.objects.filter(alumne=a, quota__any=django.utils.timezone.now().year, quota__tipus=tipus).\
                            exclude(pagament_realitzat=True).delete()
                    if crea:
                        if fracciona:
                            import1=round(float(quota.importQuota)/2.00,2)
                            import2=float(quota.importQuota)-import1
                            p=QuotaPagament(alumne=a, quota=quota, fracciona=True, importParcial=import1, dataLimit=quota.dataLimit)
                            p.save()
                            p=QuotaPagament(alumne=a, quota=quota, fracciona=True, importParcial=import2, 
                                            dataLimit=quota.dataLimit + relativedelta(months=+3))
                            p.save()
                        else:
                            p=QuotaPagament(alumne=a, quota=quota)
                            p.save()
                else:
                    # Quota esborrada
                    if pagament and not pagament.pagament_realitzat:
                        #esborrar pagament o pagaments
                        #si fracciona depén dels pagaments previs ja fets
                        if not pagament.fracciona:
                            pagament.delete()
                        else:
                            p=get_QuotaPagament(a, tipus).filter(fracciona=True)
                            if p and not p.filter(pagament_realitzat=True):
                                fraccions_esborrades=fraccions_esborrades+tuple(p.values_list('pk', flat = True))
                                p.delete()

            llista=Alumne.objects.filter(grup__curs__id=curs,
                                 data_baixa__isnull=True,
                                ).order_by('grup__nom_grup', 'cognoms', 'nom')
    
            llistapag=[]
            for a in llista:
                pagaments=get_QuotaPagament(a, tipus)
                email=a.correu_relacio_familia_pare if a.correu_relacio_familia_pare else a.correu_relacio_familia_mare
                if pagaments:
                    for pg in pagaments:
                        llistapag.append({
                            'pkp': pg.pk,
                            'pka': a.pk,
                            'cognoms': a.cognoms,
                            'nom':  a.nom ,
                            'grup': a.grup,
                            'correu': email,
                            'quota': pg.quota,
                            'estat': 'Ja pagat' if pg.pagamentFet else 'Pendent',
                            'fracciona': pg.fracciona
                            })

            if len(llistapag)==0:
                return render(
                            request,
                            'resultat.html', 
                            {'msgs': {'errors': [], 'warnings': [], 'infos': ['Sense quotes assignades']} },
                         )
            formsetQuotes = formset_factory(PagQuotesForm, extra=0)
            formset=formsetQuotes(form_kwargs={'tipus': tipus}, initial= llistapag)
            
    else:
        c=Curs.objects.get(id=curs)
        try:
            ncurs=str(int(c.nom_curs)+1)
            quotacurs=Quota.objects.filter(curs__nivell=c.nivell, curs__nom_curs=ncurs, any=django.utils.timezone.now().year, tipus=tipus)
        except:
            quotacurs=None
        
        if not quotacurs:
            # No troba una quota adequada, comprova si existeixen altres quotes del mateix tipus
            quotacurs=Quota.objects.filter(any=django.utils.timezone.now().year, tipus=tipus)
            if quotacurs.count()!=1:
                # Si troba varies no selecciona cap, si només troba una aleshores la fa servir per defecte
                quotacurs=None
                
        if quotacurs:
            quotacurs=quotacurs[0]
        else:
            quotacurs=None
        
        llista=Alumne.objects.filter(grup__curs__id=curs,
                             data_baixa__isnull=True,
                            ).order_by('grup__nom_grup', 'cognoms', 'nom')
        if not llista:
            return render(
                        request,
                        'resultat.html', 
                        {'msgs': {'errors': [], 'warnings': [], 'infos': ['Sense quotes per assignar']} },
                     )

        llistapag=[]
        for a in llista:
            pagaments=get_QuotaPagament(a, tipus)
            email=a.correu_relacio_familia_pare if a.correu_relacio_familia_pare else a.correu_relacio_familia_mare
            if pagaments:
                for pg in pagaments:
                    llistapag.append({
                        'pkp': pg.pk,
                        'pka': a.pk,
                        'cognoms': a.cognoms,
                        'nom':  a.nom,
                        'grup': a.grup,
                        'correu': email,
                        'quota': pg.quota,
                        'estat': 'Ja pagat' if pg.pagamentFet else 'Pendent',
                        'fracciona': pg.fracciona
                        })
            else:
                p=Peticio.objects.filter(alumne=a, estat='A', any=django.utils.timezone.now().year)
                if not p:
                    llistapag.append({
                        'pkp': 'None',
                        'pka': a.pk,
                        'cognoms': a.cognoms,
                        'nom':  a.nom ,
                        'grup': a.grup,
                        'correu': email,
                        'quota': quotacurs,
                        'estat': 'No assignat',
                        'fracciona': False
                        })

        if len(llistapag)==0:
            return render(
                        request,
                        'resultat.html', 
                        {'msgs': {'errors': [], 'warnings': [], 'infos': ['Sense quotes per assignar']} },
                     )
        
        formsetQuotes = formset_factory(PagQuotesForm, extra=0)
        formset=formsetQuotes(form_kwargs={'tipus': tipus}, initial= llistapag)      

            
    return render(
                  request,
                  "formsetgrid.html", 
                  { "formset": formset,
                    "head": "Assignació quotes",
                    }
                )

def acumulatsQuotes(tpv, nany=None):
    '''
    Retorna un diccionari amb tots els acumulats per quotes i mesos i quantitat pendent
    {{quota1: {'pendent':nnnnn, 1:nnnnn, 2:nnnnn, ... 12:nnnnn},
     {quota2: {'pendent':nnnnn, 1:nnnnn, 2:nnnnn, ... 12:nnnnn},
     ... }
    '''
    
    from django.db.models import Sum, Q
    
    if not nany:
        nany=django.utils.timezone.now().year
    
    totfet=QuotaPagament.objects.filter(quota__comerç=tpv, pagament_realitzat=True, data_hora_pagament__year=nany)\
                    .exclude(quota__curs__isnull=True)\
                    .values_list('quota','data_hora_pagament__month')\
                    .annotate(total=Sum('quota__importQuota', filter=Q(fracciona=False)))\
                    .annotate(totalf=Sum('importParcial', filter=Q(fracciona=True)))
    
    totpendent=QuotaPagament.objects.filter(quota__comerç=tpv, pagament_realitzat=False)\
                    .exclude(quota__curs__isnull=True)\
                    .values_list('quota')\
                    .annotate(total=Sum('quota__importQuota', filter=Q(fracciona=False)))\
                    .annotate(totalf=Sum('importParcial', filter=Q(fracciona=True)))
    
    calcul={}
    
    for p in list(totfet):
        q, m, t1, t2 = p
        tot=(t1 if t1 else 0) + (t2 if t2 else 0)
        if not q in calcul:
            calcul[q]={}
        calcul[q][m]=tot
    
    for p in list(totpendent):
        q, t1, t2 = p
        tot=(t1 if t1 else 0) + (t2 if t2 else 0)
        if not q in calcul:
            calcul[q]={}
        calcul[q]['pendent']=tot
    
    return calcul

def acumulatsTaxes(tpv, nany=None):
    '''
    Retorna un diccionari amb tots els acumulats per nivells i mesos i quantitat pendent
    {{'nivell1': {'pendent':nnnnn, 1:nnnnn, 2:nnnnn, ... 12:nnnnn},
     {'nivell2': {'pendent':nnnnn, 1:nnnnn, 2:nnnnn, ... 12:nnnnn},
     ... }
    '''
    
    from django.db.models import Sum, Q
    
    if not nany:
        nany=django.utils.timezone.now().year
    
    totfet=QuotaPagament.objects.filter(quota__comerç=tpv, pagament_realitzat=True, 
                                        data_hora_pagament__year=nany,
                                        quota__curs__isnull=True,
                                        alumne__peticio__curs__nivell__taxes__isnull=False)\
                    .values_list('alumne__peticio__curs__nivell__nom_nivell','alumne__peticio__curs__nivell__taxes__nom','data_hora_pagament__month')\
                    .annotate(total=Sum('quota__importQuota', filter=Q(fracciona=False)))\
                    .annotate(totalf=Sum('importParcial', filter=Q(fracciona=True)))
    
    totpendent=QuotaPagament.objects.filter(quota__comerç=tpv, pagament_realitzat=False, 
                                            quota__curs__isnull=True,
                                            alumne__peticio__curs__nivell__taxes__isnull=False)\
                    .values_list('alumne__peticio__curs__nivell__nom_nivell','alumne__peticio__curs__nivell__taxes__nom')\
                    .annotate(total=Sum('quota__importQuota', filter=Q(fracciona=False)))\
                    .annotate(totalf=Sum('importParcial', filter=Q(fracciona=True)))
    
    calcul={}
    
    for p in list(totfet):
        q, x, m, t1, t2 = p
        q=str(q)+'-'+str(x)
        tot=(t1 if t1 else 0) + (t2 if t2 else 0)
        if not q in calcul:
            calcul[q]={}
        calcul[q][m]=tot
    
    for p in list(totpendent):
        q, x, t1, t2 = p
        q=str(q)+'-'+str(x)
        tot=(t1 if t1 else 0) + (t2 if t2 else 0)
        if not q in calcul:
            calcul[q]={}
        calcul[q]['pendent']=tot
    
    return calcul

def fullcalculQuotes(tpv, nany=None):
    '''
    Retorna un full de càlcul xlsx amb els acumulats i pagaments pendents
    '''
    
    import xlsxwriter
    import io
    
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
    if not nany:
        nany=django.utils.timezone.now().year
    
    acumulats=acumulatsQuotes(tpv, nany)
    acumTaxes=acumulatsTaxes(tpv, nany)
    totes=Quota.objects.filter(importQuota__gt=0).values_list('id').order_by('curs__nom_curs_complert', 'descripcio')
    
    worksheet = workbook.add_worksheet('Acumulats')
    cap=['Concepte','Pendent']
    date=django.utils.timezone.now()
    for i in range(1,13):
        cap.append(date.replace(month=i, day=1).strftime('%B')[2:].strip())
    cap.append('Total Pagat')
    worksheet.set_column(0, 0, 30)
    worksheet.write_string(0,0,tpv.descripcio+'-'+str(nany)+'. Dades a '+date.strftime('%d/%m/%Y %H:%M'))
    worksheet.write_row(1,0,cap)
    fila=2
    for q in totes:
        if q[0] in acumulats:
            a = acumulats[q[0]]
            quota=Quota.objects.get(id=q[0])
            worksheet.write(fila, 0, quota.descripcio)
            for m, v in a.items():
                if m=='pendent':
                    col=1
                else:
                    col=m+1 
                worksheet.write_number(fila, col, v)
            worksheet.write_formula(fila, 14, '=SUM(C{0}:N{0})'.format(fila+1))
            fila=fila+1
    
    for t,a in acumTaxes.items():
        worksheet.write(fila, 0, t)
        for m, v in a.items():
            if m=='pendent':
                col=1
            else:
                col=m+1 
            worksheet.write_number(fila, col, v)
        worksheet.write_formula(fila, 14, '=SUM(C{0}:N{0})'.format(fila+1))
        fila=fila+1
    
    if fila>2:
        for t in range(ord('B'),ord('P')):
            worksheet.write_formula(fila, t-ord('A'), '=SUM({0}3:{0}{1})'.format(chr(t),fila))
    
    worksheet = workbook.add_worksheet('Pendents')
    worksheet.set_column(0, 4, 30)
    worksheet.write_string(0,0,'Pagaments pendents. Dades a '+date.strftime('%d/%m/%Y %H:%M'))
    worksheet.write_row(1,0,('Concepte','Alumne','Import','Data límit','Fraccionat'))
    fila=2
    pag=QuotaPagament.objects.filter(quota__comerç=tpv, pagament_realitzat=False).order_by('quota__dataLimit','quota__descripcio','alumne__cognoms','alumne__nom')
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    
    for p in pag:
        worksheet.write_string(fila, 0, p.quota.descripcio )
        worksheet.write_string(fila, 1, str(p.alumne) )
        worksheet.write_number(fila, 2, p.quota.importQuota if not p.fracciona else p.importParcial )
        worksheet.write_datetime(fila, 3, p.quota.dataLimit if not p.fracciona else p.dataLimit, date_format )
        worksheet.write_string(fila, 4, 'SI' if p.fracciona else 'NO' )
        fila=fila+1
    
    if fila>2:
        worksheet.write_formula(fila, 2, '=SUM(C3:C{0})'.format(fila))
    
    workbook.close()
    return output

@login_required
@group_required(['direcció','administradors'])
def totalsQuotes(request):
    from django.http import HttpResponse
    
    if request.method == 'POST':
        form = EscollirAny(request.POST)
        if form.is_valid():
            nany=form.cleaned_data['year']
            tpv=form.cleaned_data['tpv']
            output=fullcalculQuotes(tpv,nany)
            output.seek(0)
            filename = tpv.descripcio+'-'+str(nany)+'-quotes.xlsx'
            response = HttpResponse(
                output,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    
            return response

    else:
        form = EscollirAny()
    return render(
                request,
                'form.html', 
                {'form': form, 
                 },
                )

@login_required
@group_required(['direcció','administradors'])
def blanc( request ):
    return render(
                request,
                'blanc.html',
                    {},
                )

def creaQuotes():
    from aula.apps.sortides.models import TipusQuota, Comerç
    
    com=Comerç.objects.get(id=1)
    tip=TipusQuota.objects.get(nom='taxcurs')
    q=Quota(importQuota=360, any=django.utils.timezone.now().year, 
            descripcio='Taxes cicles FP', curs=None, comerç=com, tipus=tip)
    q.save()
    
    tip=TipusQuota.objects.get(nom='uf')
    q=Quota(importQuota=25, any=django.utils.timezone.now().year, 
            descripcio='Preu UF', curs=None, comerç=com, tipus=tip)
    q.save()
    
    com=Comerç.objects.get(id=1)
    tcomplet=Quota.objects.get(any=django.utils.timezone.now().year, tipus__nom='taxcurs')
    tuf=Quota.objects.get(any=django.utils.timezone.now().year, tipus__nom='uf')
    tip=TipusQuota.objects.get(nom='taxes')
    for quf in range(1, 15):
        tot=quf*tuf.importQuota
        if not Quota.objects.filter(importQuota=tot, any=django.utils.timezone.now().year, tipus=tip):
            q=Quota(importQuota=tot, dataLimit='2020-09-07', any=django.utils.timezone.now().year, 
                    descripcio='taxes ufs soltes', curs=None, comerç=com, tipus=tip)
            q.save()
        tot=round(float(tot)/2.00,2)
        if not Quota.objects.filter(importQuota=tot, any=django.utils.timezone.now().year, tipus=tip):
            q=Quota(importQuota=tot, dataLimit='2020-09-07', any=django.utils.timezone.now().year, 
                    descripcio='taxes ufs soltes', curs=None, comerç=com, tipus=tip)
            q.save()
    
    tot=tcomplet.importQuota
    q=Quota(importQuota=tot, dataLimit='2020-09-07', any=django.utils.timezone.now().year, 
            descripcio='taxes curs complet', curs=None, comerç=com, tipus=tip)
    q.save()
    tot=round(float(tot)/2.00,2)
    q=Quota(importQuota=tot, dataLimit='2020-09-07', any=django.utils.timezone.now().year, 
            descripcio='taxes curs complet', curs=None, comerç=com, tipus=tip)
    q.save()

def enviaIniciMat():
    for m in Preinscripcio.objects.all():
        if Nivell.objects.filter(nom_nivell=m.codiestudis, matricula_oberta=True):
            act=Peticio.objects.filter(idAlumne=m.ralc, tipusIdent='R', any=django.utils.timezone.now().year, 
                                   estat__in=('A','F',))
            if not act:
                curs=Curs.objects.get(nivell__nom_nivell=m.codiestudis, nom_curs=m.curs)
                novaPeticio=Peticio(idAlumne=m.ralc, tipusIdent='R', email=m.correu, estat='A', curs=curs)
                novaPeticio.save()
                alumne=creaAlumne(m.ralc, 'R', curs, m.correu)
                quotacurs=Quota.objects.filter(curs=novaPeticio.curs, any=novaPeticio.any, tipus__nom=settings.CUSTOM_TIPUS_QUOTA_MATRICULA)
                if quotacurs:
                    quotacurs=quotacurs[0]
                    novaPeticio.quota=quotacurs
                novaPeticio.alumne=alumne
                novaPeticio.save()
                mailPeticio(novaPeticio.estat, m.ralc, m.correu, alumne)

def gestQuotes():
    from aula.apps.sortides.models import TipusQuota, Comerç
    
    n=Nivell(nom_nivell='ACM', descripcio_nivell='ACM')
    n.save()
    c1=Curs(nom_curs='1', nom_curs_complert='ACM-1', nivell=n)
    c1.save()
    c2=Curs(nom_curs='2', nom_curs_complert='ACM-2', nivell=n)
    c2.save()
    com=Comerç.objects.get(id=1)
    tip=TipusQuota.objects.get(nom=settings.CUSTOM_TIPUS_QUOTA_MATRICULA)
    q=Quota(importQuota=111, dataLimit='2020-09-07', any=django.utils.timezone.now().year, 
            descripcio='Material,ASS.ESC. 1-ACM', curs=c1, comerç=com, tipus=tip)
    q.save()
    q=Quota(importQuota=110, dataLimit='2020-09-07', any=django.utils.timezone.now().year, 
            descripcio='Material,ASS.ESC. 2-ACM', curs=c2, comerç=com, tipus=tip)
    q.save()
    Nivell.objects.all().update(matricula_oberta=False)
    Nivell.objects.filter(nom_nivell__in=('SMX', 'ACO', 'ACM', 'GAD', 'DAW', 'ASX', 'ADF', 'GVE',)).update(matricula_oberta=True)
    Nivell.objects.all().update(taxes=None)
    tip=TipusQuota.objects.get(nom='taxes')
    Nivell.objects.filter(nom_nivell__in=('DAW', 'ASX', 'ADF', 'GVE',)).update(taxes=tip)
    Quota.objects.filter(curs__nivell__nom_nivell__in=('SMX', 'ACO', 'ACM', 'GAD', 'DAW', 'ASX', 'ADF', 'GVE',)).update(dataLimit='2020-09-07')
