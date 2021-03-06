from django.db import models
from aula.apps.alumnes.models import Alumne, Curs
from aula.apps.assignatures.models import Assignatura
from aula.apps.sortides.models import Quota, QuotaPagament
from private_storage.fields import PrivateFileField

class Dades(models.Model):
    BONIF_CHOICES=[
        ('0','Cap'),
        ('5','50%'),
        ('1','100%'),
        ]    
    nom = models.CharField("Nom alumne",max_length=50)
    cognoms = models.CharField("Cognoms alumne",max_length=100)
    centre_de_procedencia = models.CharField("Centre de procedència", max_length=50, null=True, blank=True)
    data_naixement = models.DateField("Data de naixement")
    alumne_correu = models.EmailField("Correu de l'alumne", help_text = u'Correu de notificacions de l\'alumne', null=True)
    adreca = models.CharField("Adreça", max_length=250)
    localitat = models.CharField("Localitat", max_length=250)
    cp = models.CharField("Codi postal", max_length=10)
    rp1_nom = models.CharField("Nom complet 1r responsable", max_length=250) #responsable 1
    rp1_telefon1 = models.CharField("Telèfon 1r responsable", max_length=15)
    rp1_correu = models.EmailField( "Correu 1r responsable")
    rp2_nom = models.CharField("Nom complet 2n responsable", max_length=250, null=True, blank=True) #responsable 2
    rp2_telefon1 = models.CharField("Telèfon 2n responsable", max_length=15, null=True, blank=True)
    rp2_correu = models.EmailField( "Correu 2n responsable", null=True, blank=True)
    files = PrivateFileField("Fitxer amb documents", upload_to='matricula/%Y/', max_file_size=20000000, null=True, 
                             help_text='Documentació obligatòria')
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    acceptar_condicions=models.BooleanField("Accepto condicions de matrícula")
    curs_complet=models.BooleanField("Matrícula del curs complet", help_text = 'Matrícula típica de totes les UFs', default=False)
    quantitat_ufs=models.IntegerField("UFs soltes, curs no complet", null=True, blank=True, default=0)
    bonificacio=models.CharField("Tipus de bonificació taxes", max_length=1, choices=BONIF_CHOICES, default='0')
    llistaufs = models.CharField("Mòduls i ufs de la matrícula", help_text = 'En cas de UFs soltes', max_length=250, null=True, blank=True)
    fracciona_taxes=models.BooleanField("Fracciona pagament taxes", default=False)
    
    class Meta:
        verbose_name = u'Dades'
        verbose_name_plural = u'Dades' 
              
    def __str__(self):
        return self.nom+' '+self.cognoms
    
    @property
    def pagamentFet(self):
        pag=self.getPagament
        if pag:
            for p in pag:
                if not p.pagamentFet: return False
            return True
        return False
    
    @property
    def getPagament(self):
        #p=QuotaPagament.objects.filter(alumne=self.peticio.alumne, quota=self.peticio.quota)
        p=QuotaPagament.objects.filter(alumne=self.peticio.alumne, quota__any=self.peticio.any)
        return p

class UFS(models.Model):
    alumne=models.ForeignKey(Alumne, on_delete=models.PROTECT)
    modul=models.ForeignKey(Assignatura, on_delete=models.PROTECT)
    numero=models.IntegerField()
    
    class Meta:
        unique_together = ('alumne','modul','numero')
        ordering = ['alumne','modul','numero']
        
    def __str__(self):
        return str(self.alumne)+' '+str(self.modul)+' '+str(self.numero)

class Peticio(models.Model):
    import aula.apps.sortides.models
    TIPUS_CHOICES=[
        ('R','RALC'),
        ('D','DNI'),
        ]
    ESTAT_CHOICES=[
        ('P','Pendent'),
        ('R','Rebutjada'),
        ('D','Duplicada'),
        ('A','Acceptada'),
        ('F','Finalitzada'),
        ]
    idAlumne=models.CharField("RALC de l'alumne", max_length=15, help_text='DNI si l\'alumne no té RALC')
    tipusIdent=models.CharField("Tipus d'identificació", max_length=1, choices=TIPUS_CHOICES,  default='R')
    email=models.EmailField("Correu de contacte")
    any=models.IntegerField(default=aula.apps.sortides.models.return_any_actual)
    estat=models.CharField( max_length=1, choices=ESTAT_CHOICES, default='P')
    curs = models.ForeignKey(Curs, verbose_name="Curs on matricular-se", on_delete=models.PROTECT)
    quota=models.ForeignKey(Quota, on_delete=models.PROTECT, null=True, blank=True)
    alumne=models.ForeignKey(Alumne, on_delete=models.PROTECT, null=True, blank=True)
    dades=models.OneToOneField(Dades, on_delete=models.PROTECT, null=True, blank=True)
    
    class Meta:
        #unique_together = ('any','idAlumne')
        ordering = ['pk']
        verbose_name = u'Peticio'
        verbose_name_plural = u'Peticions'
              
    def __str__(self):
        return self.tipusIdent +':'+ self.idAlumne +' '+ str(self.estat) +' '+ str(self.email)
    