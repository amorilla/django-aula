# This Python file uses the following encoding: utf-8
import random
from aula.apps.usuaris.models import OneTimePasswd, Professor, Accio
from django.utils.datetime_safe import datetime
from datetime import timedelta
from django.db.models import Q
from django.conf import settings
from aula.apps.alumnes.models import Alumne
import re
import dns.resolver
import smtplib
import imaplib
import email
from django.contrib.auth.models import User, Group
from aula.apps.missatgeria.models import Missatge
from aula.apps.missatgeria.missatges_a_usuaris import tipusMissatge, MAIL_REBUTJAT

def connectIMAP():
    '''
    Realitza connexió al servidor de correu segons les dades 
    dels settings EMAIL_HOST_IMAP EMAIL_HOST_USER EMAIL_HOST_PASSWORD
    
    Retorna objecte IMAP4_SSL per accedir al correu o None si falla
    
    '''
    
    mail = imaplib.IMAP4_SSL(settings.EMAIL_HOST_IMAP)
    if mail:
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.select()
    return mail

def disconnectIMAP(mail):
    '''
    Desconnecta el servidor de correu IMAP mail
    
    '''
    
    if mail:
        try:
            mail.close()
            mail.logout()
        except:
            pass

def extractEmail(address):
    '''
    Comprova o recupera una adreça email de l'string address
    Només fa la comprovació sintàctica, si l'string és format per varies 
    adreces potencials retorna la primera correcta
    
    Retorna True, adreçaOK si és vàlid
            False, address original si no correspon a email 
            
    '''
    
    addressToVerify=address.strip().lower()
    splitAddress = addressToVerify.split(' ')
    for a in splitAddress:
        # General Email Regex (RFC 5322 Official Standard)
        regex= '(?:[a-z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&\'*+/=?^_`{|}'\
               '~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\['\
               '\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])'\
               '?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]'\
               '?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]'\
               '*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])'
        match = re.match(regex, a)
        if match:
            return True, a
    #Email Syntax Error      
    return False, address

def testEmail(addressToVerify, testMailbox=False):
    '''
    Verifica si una adreça de correu és correcta
    Comprova sintaxis i domini vàlid.
    Si testMailbox és True també consulta al servidor corresponent, només 
    té en compte el cas 550 Non-existent email address. Altres casos no es consideren error.
    
    Retorna  0, adreçaOK  si s'ha obtingut una adreça vàlida
            -1, addressToVerify  si l'adreça és '' o None
            -2, addressToVerify  si sintaxis incorrecte
            -3, addressToVerify  si domini incorrecte
            -4, addressToVerify  si mailbox inexistent (codi 550)
    
    '''
    
    if not addressToVerify: return -1, addressToVerify
    
    valida, addressToVerify=extractEmail(addressToVerify)
    if not valida:
        return -2, addressToVerify
    
    splitAddress = addressToVerify.split('@')
    domain = str(splitAddress[1])
    try:
        records = dns.resolver.query(domain, 'MX')
        mxRecord = records[0].exchange
        mxRecord = str(mxRecord)
    except:
        #print('Domain Error',addressToVerify)
        return -3, addressToVerify
    
    if not testMailbox:
        return 0, addressToVerify
    
    # SMTP Conversation
    try:
        server = smtplib.SMTP(timeout=10)
        server.set_debuglevel(0)
        server.connect(mxRecord)
        server.helo(server.local_hostname)
        fromEmail=settings.DEFAULT_FROM_EMAIL.split(" ")
        fromEmail=fromEmail[len(fromEmail)-1]
        fromEmail=fromEmail[1:len(fromEmail)-1]
        
        code, _ = server.docmd("MAIL", "FROM:<%s>" % fromEmail)
        code, _ = server.docmd("RCPT", "TO:<%s>" % str(addressToVerify))
        
        server.quit()
        server.close()
    except:
        #print('Mailbox Error', addressToVerify);
        #No es pot identificar el problema, es considera vàlida
        return 0, addressToVerify
    
    if code == 550:
        # 550 Non-existent email address
        #print('Mailbox Error', addressToVerify, code);
        return -4, addressToVerify
    
    return 0, addressToVerify


def datemailTodatetime(dateEmail):
    '''
    Retorna objecte datetime a partir d'un string IMAP4 INTERNALDATE
    '''
    
    date=None
    if dateEmail:
        date_tuple=email.utils.parsedate_tz(dateEmail)
        if date_tuple:
            date=datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
    return(date)

def getEmailText(msg):
    '''
    Retorna el text del missatge dins de l'objecte email.message.Message msg
    
    for part in message.walk():
        if part.get('content-disposition', '').startswith('attachment;'):
            continue
        if part.get_content_maintype() == maintype and \
                part.get_content_subtype() == subtype:
            charset = part.get_content_charset()
            this_part = part.get_payload(decode=True)
            if charset:
                try:
                    this_part = this_part.decode(charset, 'replace')
                except LookupError:
                    this_part = this_part.decode('ascii', 'replace')
    
    '''
    
    if msg is None or not msg.is_multipart():
        return ''
    else: 
        for m in msg.get_payload():
            if m.is_multipart():
                return getEmailText(m)
            if m.get_content_maintype() == 'text':
                    text=m.get_payload(None,True)
                    subject=m.get('subject')
                    try:
                        return str(subject)+":\n"+text.decode("utf-8")
                    except:
                        return str(subject)+":\n"+text
        return ''

def getMailsList(mail, data=None):
    '''
    Retorna la llista dels identificadors de
    correus rebuts al servidor mail. 
    Es farà servir per al fetch de cada correu.
    
    '''
    months=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    if data:
        data=data-timedelta(days=1)
    else:
        data=datetime.now()-timedelta(days=10)
    data=str(data.day)+"-"+months[data.month-1]+"-"+str(data.year)
    id_list=None
    if mail:
        #_ , dades = mail.search(None, 'ALL')
        #print(data)
        _ , dades = mail.search(None, '(SENTSINCE "'+data+'")' )
        mail_ids = dades[0]
        id_list = mail_ids.split()
    return id_list

def informaDSN2(destinataris,usuari,emailRetornat,motiu,data):
    al=Alumne.objects.filter(user_associat=usuari)
    if al.exists():
        al=al[0]
        mostra=False
        
        if (al.correu_relacio_familia_pare==emailRetornat):
            mostra=True
            al.correu_relacio_familia_pare=''
        if (al.correu_relacio_familia_mare==emailRetornat):
            mostra=True
            al.correu_relacio_familia_mare=''
        '''
        if (al.rp1_correu==emailRetornat):
            mostra=True
            al.rp1_correu=''
        if (al.rp2_correu==emailRetornat):
            mostra=True
            al.rp2_correu=''
        if (al.correu_tutors==emailRetornat):
            mostra=True
            al.correu_tutors=''
        if (al.correu==emailRetornat):
            mostra=True
            al.correu=''
        '''
        if mostra:
            #al.save()
            print(str(al.ralc)+";"+str(al.grup)+";"+str(al)+";"+emailRetornat+";"+str(data))

def informaDSN(destinataris,usuari,emailRetornat,motiu,data):
    '''
    Envia missatges Djau per cada destinatari
    Informa de l'error de l'adreça email de l'usuari
    Si l'usuari s'ha connectat des de la data aleshores també rep el missatge
    
    '''
    
    #print(str(usuari)+";"+emailRetornat+";"+str(data))
    
    enviaUsuari=False
    if not destinataris or not usuari:
        destinataris= Group.objects.get_or_create( name = 'administradors' )[0].user_set.all()
    if usuari:
        #  Si usuari u s'ha connectat des de la data aleshores també se li comunica
        connexions = usuari.LoginUsuari.filter(exitos=True).order_by( '-moment' )
        if connexions.exists():
            dataDarreraConnexio = connexions[0].moment
            if dataDarreraConnexio>data:
                enviaUsuari=True
    
    missatge = MAIL_REBUTJAT.format(str(usuari) if usuari else "desconegut", emailRetornat, str(data), motiu)
    tipus_de_missatge = tipusMissatge(missatge)
    usuari_notificacions, new = User.objects.get_or_create( username = 'TP')
    if new:
        usuari_notificacions.is_active = False
        usuari_notificacions.first_name = u"Usuari Tasques Programades"
        usuari_notificacions.save()
    msg = Missatge( remitent = usuari_notificacions, text_missatge = missatge, tipus_de_missatge = tipus_de_missatge  )
    for d in destinataris:
        msg.envia_a_usuari( d , 'VI')
    if enviaUsuari:
        pass
        #msg.envia_a_usuari( usuari , 'VI')

def informa(emailRetornat, status, action, data, diagnostic, text):
    '''
    Si el email retornat correspon a un alumne --> notifica al tutor
    Si correspon a un altre --> notifica als administradors
    motiu <-- status + action + diagnostic

    '''
    
    motiu=status+" "+ action +" "+ diagnostic
    # Fa recerca de l'usuari al text del missatge rebutjat
    pos=text.find("recoverPasswd")
    if pos!=-1:
        usuari=text[pos:].split("/")[1].strip()
    else:
        pos=text.find("nom d'usuari és")
        if pos!=-1:
            pos1=pos+len("nom d'usuari és")
            pos2=text.find("Per qualsevol dubte que")
            usuari=text[pos1:pos2].split(":")[1].strip()
        else:
            usuari=None
    
    altre=None
    administradors = Group.objects.get_or_create( name = 'administradors' )[0].user_set.all()
    if usuari is None:
        #és usuari desconegut
        correus = (Q( correu_relacio_familia_pare = emailRetornat ) |
            Q( correu_relacio_familia_mare = emailRetornat ) | Q(correu_tutors = emailRetornat) |
            Q(rp1_correu = emailRetornat) | Q(rp2_correu = emailRetornat) | Q(correu = emailRetornat))
        alumnes=Alumne.objects.filter(correus).filter(data_baixa__isnull = True).distinct()
        if alumnes.exists():
            #Cada alumne amb el seu tutor
            #envia a tots els tutors que corresponguin --> notifica usuaris, email, motiu
            for almn in alumnes:
                if almn.correu_relacio_familia_pare == emailRetornat or almn.correu_relacio_familia_mare == emailRetornat:
                    tutors=almn.tutorsDelGrupDeLAlumne()
                    informaDSN(tutors,almn.get_user_associat(),emailRetornat,motiu,data)
                else:
                    informaDSN(administradors,almn.get_user_associat(),emailRetornat,motiu,data)
            return
        else:
            altre=User.objects.filter(email = emailRetornat)
            altre=altre[0] if altre.exists() else None
    else:
        altre=User.objects.filter(username = usuari)
        if altre.exists():
            altre=altre[0]
            try:
                almn=Alumne.objects.get(user_associat=altre, data_baixa__isnull = True)
            except:
                almn=None
            if almn:
                #és un alumne
                #determina tutor, notifica al tutor usuari, email, motiu
                if almn.correu_relacio_familia_pare == emailRetornat or almn.correu_relacio_familia_mare == emailRetornat:
                    tutors=almn.tutorsDelGrupDeLAlumne()
                    informaDSN(tutors,almn.get_user_associat(),emailRetornat,motiu,data)
                else:
                    informaDSN(administradors,almn.get_user_associat(),emailRetornat,motiu,data)
                return
        else: 
            altre=None
            motiu="Desconegut "+usuari+"\n"+motiu
    #no és un alumne envia notificació a administradors
    #notificació usuari, email, motiu
    informaDSN(administradors,altre,emailRetornat,motiu,data)

def controlDSN(dies=15):
    '''
    Verifica si s'han rebut correus d'error delivery status notification (DSN) a partir
    de l'ultima vegada. Si és el primer control aleshores comprova els últims 15 dies.
    Per cada correu identifica destinatari erroni i informa al tutor o a l'administrador de Django.
    
    Retorna True si ok o False si no pot accedir al correu
    '''
    
    ultimControl=Accio.objects.filter(tipus='DS').order_by( '-moment' )
    if ultimControl.exists():
        ultimaVegada=ultimControl[0].moment
        ultimFetch=ultimControl[0].text.split(";")[1].encode()
    else:
        ultimaVegada=datetime.now() - timedelta(days=dies)
        ultimFetch=b'0';
    mail=connectIMAP()
    if mail is None: return False
    id_list=getMailsList(mail, ultimaVegada)
    if id_list is None: return False
    i=len(id_list)-1
    num=id_list[i]
    #print(str(id_list))
    while num!=ultimFetch and i>=0:
        status, data = mail.fetch(num, '(RFC822)' )
        # the content data at the '(RFC822)' format comes on
        # a list with a tuple with header, content, and the closing
        # byte b')'
        for response_part in data:
            # so if its a tuple...
            if isinstance(response_part, tuple):
                # we go for the content at its second element
                # skipping the header at the first and the closing
                # at the third
                msg = email.message_from_bytes(response_part[1])
                if (msg.is_multipart() and len(msg.get_payload()) > 1 and 
                    msg.get_payload(1).get_content_type() == 'message/delivery-status'):
                    # email is DSN
                    for m in msg.get_payload():
                        if m.get_content_type() == 'message/rfc822':
                            text=getEmailText(m)
                            break
                    for dsn in msg.get_payload(1).get_payload():
                        if dsn.get_content_type() == 'text/plain':
                            fr=dsn.get('Final-Recipient')
                            if fr: emailRetornat=fr.split(';')[1].strip()
                            st=dsn.get('status')
                            if st: status=st
                            act=dsn.get('action')
                            if act: action=act
                            ad=dsn.get('Arrival-Date')
                            if ad: data=datemailTodatetime(ad)
                            dc=dsn.get('diagnostic-code')
                            if dc: diagnostic=dc.split(';')[1]
                    informa(emailRetornat, status, action, data, diagnostic, text)
        i=i-1
        if i>=0: num=id_list[i]
    
    usuari_notificacions, new = User.objects.get_or_create( username = 'TP')
    if new:
        usuari_notificacions.is_active = False
        usuari_notificacions.first_name = u"Usuari Tasques Programades"
        usuari_notificacions.save()
    Accio.objects.create( 
            tipus = 'DS',
            usuari = usuari_notificacions,
            l4 = False,
            impersonated_from = None,
            text = u"Comprovació emails rebutjats. ;"+str(id_list[len(id_list)-1].decode())
            )   
    
    disconnectIMAP(mail)
    return True


def enviaOneTimePasswd( email ):
    q_correu_pare = Q( correu_relacio_familia_pare = email )
    q_correu_mare = Q( correu_relacio_familia_mare = email )    
    nUsuaris = 0
    nErrors = 0
    errors = []
    alumnes = Alumne.objects.filter( q_correu_pare | q_correu_mare )
    for alumne in alumnes:
        resultat = enviaOneTimePasswdAlumne( alumne )
        nUsuaris += 1
        if resultat['errors']:
            nErrors += 1 
            errors.append( ', '.join( resultat['errors'] ) )

    professors = Professor.objects.filter( email = email )
    for professor in professors:
        resultat = enviaOneTimePasswdProfessor(professor)
        nUsuaris += 1
        if resultat['errors']:
            nErrors += 1 
            errors.append( ', '.join( resultat['errors'] ) )
    
    return   {  'errors':   [ u"Hi ha hagut errors recuperant la contrasenya:",  ] + errors 
                            if nErrors>0 else [], 
                'infos':    [ u"{0} correus enviats.".format( nUsuaris - nErrors  ), 
                              u"Comprovi la seva bústia de correu." ] 
                            if nUsuaris - nErrors > 0 else [],
                'warnings': [ u"No és possible recuperar aquest compte.", 
                              u"Revisi l'adreça informada." ,
                              u"Contacti amb el tutor o amb el cap d'estudis."  ] 
                            if nUsuaris == 0 else [], }        

def enviaOneTimePasswdAlumne( alumne, force = False ):
    
    usuari = alumne.get_user_associat().username
    actiu =  alumne.esta_relacio_familia_actiu()     
    correusFamilia = alumne.get_correus_relacio_familia()
        
    infos = []
    warnings = []
    errors = []
    
    #comprovo que no s'hagi enviat més de 2 recuperacions en un dia:
    fa_24h = datetime.now() - timedelta( days = 1 )
    total_enviats = OneTimePasswd.objects.filter( usuari =alumne.user_associat, moment_expedicio__gte = fa_24h  ).count()
    if total_enviats >= 3:
        errors.append( u'Màxim número de missatges enviats a aquest correu durant les darrers 24h.' )
    elif not correusFamilia:
        warnings.append( u"Comprova que l'adreça electrònica d'almenys un dels pares estigui informada")
        errors.append( u"Error enviant codi de recuperació d'accés" )
    elif alumne.esBaixa():
        warnings.append( u"Aquest alumne és baixa. No se li pot enviar codi d'accés.")
        errors.append( u"Error enviant codi de recuperació d'accés")
    else:
        #preparo el codi a la bdd:
        clau = str( random.randint( 100000, 999999) ) + str( random.randint( 100000, 999999) )
        OneTimePasswd.objects.create(usuari = alumne.user_associat, clau = clau)
        
        #envio missatge:
        urlDjangoAula = settings.URL_DJANGO_AULA
        url = "{0}/usuaris/recoverPasswd/{1}/{2}".format( urlDjangoAula, usuari, clau )
        txtCapcelera = u"Enviat missatge a {0} .".format( 
                                u", ".join( correusFamilia )
                                                                )
        infos.append(txtCapcelera)
        assumpte = u"{0} - Recuperar/Obtenir accés a l'aplicatiu Djau de {1}".format(alumne.nom, settings.NOM_CENTRE )
        missatge = [
                     u"Aquest missatge ha estat enviat per un sistema automàtic. No responguis  a aquest e-mail, el missatge no serà llegit per ningú.",
                     u"",
                     u"Per qualsevol dubte/notificació posa't en contacte amb el tutor/a.",
                     u"",
                     u"La pàgina principal del portal de relació amb famílies de l'Institut és:",
                     u"{0}".format( urlDjangoAula ),
                     u"El vostre codi d'usuari és: **  {0}  **".format( usuari ),
                     u"",
                     u"Si no disposeu de contrasenya, podeu obtenir accés al portal de {0} amb aquest enllaç:".format(alumne.nom),
                     u"{0}".format( url ),
                     u"",
                     u"Aquest enllaç romandrà operatiu durant 30 minuts.",
                     u"", 
                     u"""Instruccions:""",
                     u"Punxeu o copieu l'enllaç al vostre navegador. El sistema us tornarà a informar del vostre nom d'usuari ({0}) ".format( usuari ),
                     u"i us preguntarà quina contrasenya voleu. Com a mesura suplementària de seguretat us demanarà també alguna altre dada.",
                     u"Recordeu usuari i contrasenya per futures connexions al portal de relació amb famílies.",
                     u"  ",
                     u"Cordialment,",
                     u"  ",
                     settings.NOM_CENTRE,
                    ]
    
        from django.core.mail import send_mail
        enviatOK = True
        try:
            fromuser = settings.DEFAULT_FROM_EMAIL
            send_mail(assumpte, 
                      u'\n'.join( missatge ), 
                      fromuser,
                      [ x for x in [ alumne.correu_relacio_familia_pare, alumne.correu_relacio_familia_mare] if x is not None ], 
                      fail_silently=False)
            infos.append('Missatge enviat correctament.')
        except:
            infos = []
            enviatOK = False
        
        if not enviatOK:
            errors.append( u'Hi ha hagut un error enviant la passwd.'  )
        
    return   {  'errors':  errors, 'infos': infos, 'warnings':warnings, }



def enviaOneTimePasswdProfessor( professor, force = False ):
    
    usuari = professor.getUser().username
    correu = professor.getUser().email
        
    infos = []
    warnings = []
    errors = []
    
    #comprovo que no s'hagi enviat més de 2 recuperacions en un dia:
    fa_24h = datetime.now() - timedelta( days = 1 )
    total_enviats = OneTimePasswd.objects.filter( usuari =professor.getUser(), moment_expedicio__gte = fa_24h  ).count()
    if total_enviats >= 3:
        errors.append( u'Màxim número de missatges enviats a aquest correu durant les darrers 24h.' )
    elif not correu:
        warnings.append( u"Comprova que l'adreça electrònica d'aquest professor estigui informada")
        errors.append( u"Error enviant codi de recuperació d'accés" )
#    elif not professor.getUser().is_active:
#        warnings.append( u"Aquest professor no és actiu. No se li pot enviar codi d'accés.")
#        errors.append( u"Error enviant codi de recuperació d'accés")
    else:
        #preparo el codi a la bdd:
        clau = str( random.randint( 100000, 999999) ) + str( random.randint( 100000, 999999) )
        OneTimePasswd.objects.create(usuari = professor.getUser(), clau = clau)
        
        #envio missatge:
        urlDjangoAula = settings.URL_DJANGO_AULA
        url = "{0}/usuaris/recoverPasswd/{1}/{2}".format( urlDjangoAula, usuari, clau )
        txtCapcelera = u"Enviat missatge a {0} .".format( 
                                correu
                                                                )
        infos.append(txtCapcelera)
        missatge = [ 
                     u"La pàgina principal del programa de relació famílies de l'Institut és:",
                     u"{0}".format( urlDjangoAula ),
                     u"El vostre codi d'usuari és: **  {0}  **".format( usuari ),
                     u"",
                     u"Si no disposeu de contrasenya, podeu obtenir accés al portal de {0} amb aquest enllaç:".format(professor.getUser().first_name),
                     u"{0}".format( url ),
                     u"",
                     u"Aquest enllaç romandrà operatiu durant 30 minuts.",
                     u"", 
                     u"""Instruccions:""",
                     u"Punxeu o copieu l'enllaç al vostre navegador. El sistema us tornarà a informar del vostre nom d'usuari ({0}) ".format( usuari ),
                     u"i us preguntarà quina contrasenya voleu. Com a mesura suplementària de seguretat us demanarà també alguna altre dada.",
                     u"Recordeu usuari i contrasenya per futures connexions a l'aplicatiu.",
                     u"  ",
                     settings.NOM_CENTRE,
                    ]
    
        from django.core.mail import send_mail
        enviatOK = True
        try:
            fromuser = settings.DEFAULT_FROM_EMAIL
            send_mail(u"Accés a l'aplicatiu de {0}".format( settings.NOM_CENTRE), 
                      u'\n'.join( missatge ), 
                      fromuser,
                      [  correu ] , 
                      fail_silently=False)
            infos.append('Missatge enviat correctament.')
        except:
            infos = []
            enviatOK = False
        
        if not enviatOK:
            errors.append( u'Hi ha hagut un error enviant la passwd.'  )
        
    return   {  'errors':  errors, 'infos': infos, 'warnings':warnings, }


def enviaBenvingudaAlumne( alumne, force = False ):
        
    correusFamilia = alumne.get_correus_relacio_familia()
        
    infos = []
    warnings = []
    errors = []
    
    if not correusFamilia:
        warnings.append( u"Comprova que l'adreça electrònica d'almenys un dels pares estigui informada")
        errors.append( u"Error enviant correu de benvinguda" )
    elif alumne.esBaixa():
        warnings.append( u"Aquest alumne és baixa. No se li pot enviar codi d'accés.")
        errors.append( u"Error enviant correu de benvinguda")
    else:
        #envio missatge:
        urlDjangoAula = settings.URL_DJANGO_AULA
        textTutorial = settings.CUSTOM_PORTAL_FAMILIES_TUTORIAL 
        
        txtCapcelera = u"Enviat missatge a {0} .".format( 
                                u", ".join( correusFamilia )
                                                                )
        infos.append(txtCapcelera)
        assumpte = u"Alta a l'aplicatiu Djau de {0}".format( settings.NOM_CENTRE )

        missatge = [ u"Aquest missatge ha estat enviat per un sistema automàtic. No responguis  a aquest e-mail, el missatge no serà llegit per ningú.",
                     u"",
                     u"Per qualsevol dubte/notificació posa't en contacte amb el tutor/a.",
                     u"",
                     u"Benvolgut/da,",
                     u"",
                     u"El motiu d'aquest correu és el de donar-vos les instruccions d'alta de l'aplicació Djau del nostre centre.",
                     u"Aquesta aplicació us permetrà fer un seguiment diari del rendiment acadèmic del vostre fill/a.",
                     u"Per tant, hi trobareu les faltes d'assistència, de disciplina, les observacions del professorat , les sortides que afectaran al vostre fill/a entre altres informacions.",
                     u"",
                     u"Per a donar-vos d'alta:",
                     u"",
                     u" * Entreu a {0} on podeu obtenir o recuperar les claus d'accés a l'aplicació.".format(urlDjangoAula),
                     u" * Cliqueu l'enllaç 'Obtenir o recuperar accés'. ",
                     u" * Escriviu la vostra adreça de correu electrònic.",
                     u" * Cliqueu el botó  Enviar.",
                     u" * Consulteu el vostre correu electrònic on hi trobareu un missatge amb les instruccions per completar el procés d'accés al Djau.",
                     u"",
                     u"Com bé sabeu és molt important que hi hagi una comunicació molt fluida entre el centre i les famílies.",
                     u"És per això que us recomanem que us doneu d'alta a aquesta aplicació i per qualsevol dubte que tingueu al respecte, poseu-vos en contacte amb el tutor/a del vostre fill/a.",
                     u"",
                     u"Restem a la vostra disposició per a qualsevol aclariment.",
                     u"",
                     u"Cordialment,",
                     u"",
                     settings.NOM_CENTRE,
                     u"",
                     u"{0}".format( textTutorial ), 
                     ]        
        
      
    
        from django.core.mail import send_mail
        enviatOK = True
        try:
            fromuser = settings.DEFAULT_FROM_EMAIL
            send_mail(assumpte, 
                      u'\n'.join( missatge ), 
                      fromuser,
                      [ x for x in [ alumne.correu_relacio_familia_pare, alumne.correu_relacio_familia_mare] if x is not None ], 
                      fail_silently=False)
            infos.append('Missatge enviat correctament.')
        except:
            infos = []
            enviatOK = False
        
        if not enviatOK:
            errors.append( u'Hi ha hagut un error enviant la benvinguda.'  )
        
    return   {  'errors':  errors, 'infos': infos, 'warnings':warnings, }


def bloqueja( alumne, motiu ):
    actiu =  alumne.esta_relacio_familia_actiu() 

    infos = []
    warnings = []
    errors = []
        
    if actiu and alumne.get_user_associat() is not None and alumne.user_associat.is_active:
        alumne.user_associat.is_active = False
        alumne.user_associat.save()
        alumne.motiu_bloqueig = motiu
        #alumne.credentials = credentials
        alumne.save()
        infos.append(u'Accés desactivat amb èxit.')    
    return   {  'errors':  errors, 'infos': infos, 'warnings':warnings, }

def desbloqueja( alumne ):
    actiu =  alumne.esta_relacio_familia_actiu() 

    infos = []
    warnings = []
    errors = []
        
    if not actiu:
        #Si no té user associat en creo un:
        usuari_associat = alumne.get_user_associat()
        
        #Desbloquejo: 
        esPotDesbloquejar = alumne.get_correus_relacio_familia() \
                            and usuari_associat is not None \
                            and not alumne.esBaixa()
        if esPotDesbloquejar:
            usuari_associat.is_active = True
            usuari_associat.save()
            alumne.motiu_bloqueig = u''
            #alumne.credentials = credentials
            alumne.save()
            infos.append(u'Accés activat amb èxit.')
        else:
            errors.append(u'No es pot desbloquejar, comprova que té adreça de correu dels pares i no és baixa.')
   
    return   {  'errors':  errors, 'infos': infos, 'warnings':warnings, }


