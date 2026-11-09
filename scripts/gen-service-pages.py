# -*- coding: utf-8 -*-
"""Génère les pages contact / charte éditoriale / cookies manquantes des sites de la vague 2.

Ces trois pages sont référencées par routes.ts et liées depuis l'encart auteur de
chaque page (PageLayout), mais n'avaient jamais été écrites : tous les sites
servaient donc des 404 sur chaque page. Le plan §2.2 les exige (« À propos /
Impressum / Confidentialité / Contact ») et §2.6 exige la traçabilité éditoriale.
"""
import os, re, sys

# Ancien générateur (vague 2). Depuis la décision du 2026-10-17 (GA4 avec cookies), la page cookies
# d'un site se fait avec gen-legal-pages.py, qui dit vrai avec ou sans GA4_ID.
# Règle du 2026-10-06 : aucun cookie, aucun bandeau, ni Google Analytics ni publicité ;
# seule mesure = Microsoft Clarity sans cookie (page cookies et encart « financement »).
# Essai sans toucher aux sites : GEN_SERVICE_ROOT=/chemin/vers/dossier-test python3 gen-service-pages.py
ROOT = os.environ.get('GEN_SERVICE_ROOT', '/Users/mottalib/Documents/simulateurs-2026')

# subject      : le sujet du site, décliné dans la langue
# authority    : l'organisme qui décide en dernier ressort (pour « nous ne conseillons pas »)
# official     : (nom, url) de l'outil ou de la page officielle servant de contre-vérification
# regulator    : autorité de protection des données compétente
# social_body  : l'organisme à qui renvoyer les questions individuelles
SITES = {
    'ca-ei-calculator': {
        'langs': {'en': dict(
            subject='Employment Insurance benefits',
            authority='Service Canada',
            official=('Service Canada – EI benefits', 'https://www.canada.ca/en/services/benefits/ei.html'),
            regulator='the Office of the Privacy Commissioner of Canada',
            law='Canada’s PIPEDA',
            sources=[('Service Canada', 'weekly benefit rates, maximum insurable earnings and the regional unemployment rate table'),
                     ('Statistics Canada', 'the monthly unemployment rates that drive the 62 EI economic regions'),
                     ('the Canada Revenue Agency', 'the tax treatment of benefits and the repayment threshold')],
            fields=['your gross insurable earnings and the number of insurable hours',
                    'your EI economic region or postal code', 'the number of best weeks used',
                    'whether you claimed the Family Supplement'],
        ), 'fr': dict(
            subject='prestations d’assurance-emploi',
            authority='Service Canada',
            official=('Service Canada – Assurance-emploi', 'https://www.canada.ca/fr/services/prestations/ae.html'),
            regulator='le Commissariat à la protection de la vie privée du Canada',
            law='la LPRPDE',
            sources=[('Service Canada', 'les taux de prestation, le maximum de la rémunération assurable et le tableau des taux de chômage régionaux'),
                     ('Statistique Canada', 'les taux de chômage mensuels qui pilotent les 62 régions économiques'),
                     ('l’Agence du revenu du Canada', 'le traitement fiscal des prestations et le seuil de remboursement')],
            fields=['votre rémunération assurable brute et le nombre d’heures assurables',
                    'votre région économique ou votre code postal', 'le nombre de semaines de rémunération les plus élevées retenues',
                    'le fait d’avoir demandé ou non le supplément familial'],
        )}},
    'au-final-pay': {
        'langs': {'en': dict(
            subject='final pay, redundancy and long service leave',
            authority='the Fair Work Commission',
            official=('the Fair Work Ombudsman', 'https://www.fairwork.gov.au/'),
            regulator='the Office of the Australian Information Commissioner',
            law='the Australian Privacy Act 1988',
            sources=[('the Fair Work Act 2009 and the National Employment Standards', 'notice periods and the redundancy pay scale'),
                     ('each state and territory long service leave Act', 'the accrual rates and the pro-rata thresholds'),
                     ('the Australian Taxation Office', 'the tax-free limit, ETP caps and the withholding rates applied on termination')],
            fields=['your base rate of pay and whether it is weekly, fortnightly or annual',
                    'your years of continuous service, to one decimal place', 'your state or territory',
                    'the accrued annual leave and long service leave balances you entered'],
        )}},
    'nl-ww-berekenen': {
        'langs': {'nl': dict(
            subject='de WW-uitkering en de transitievergoeding',
            authority='het UWV',
            official=('het UWV', 'https://www.uwv.nl/'),
            regulator='de Autoriteit Persoonsgegevens',
            law='de AVG',
            sources=[('het UWV', 'de dagloonregels, het maximumdagloon en de duur van de uitkering'),
                     ('de Belastingdienst', 'de loonheffingstabellen en de heffingskortingen'),
                     ('Rijksoverheid en wetten.nl', 'de wettekst van de Werkloosheidswet en van boek 7 BW over de transitievergoeding')],
            fields=['het SV-loon over het refertejaar en het aantal gewerkte uren',
                    'de datum waarop het dienstverband eindigde', 'het arbeidsverleden in jaren',
                    'of u de loonheffingskorting laat toepassen'],
        )}},
    'de-arbeitslosengeld': {
        'langs': {'de': dict(
            subject='das Arbeitslosengeld I',
            authority='die Agentur für Arbeit',
            official=('der Selbstberechnungsbogen der Bundesagentur für Arbeit', 'https://www.arbeitsagentur.de/'),
            regulator='die zuständige Landesdatenschutzbehörde',
            law='die DSGVO und das BDSG',
            sources=[('die Bundesagentur für Arbeit', 'die Leistungsentgeltverordnung und die Anspruchsdauer nach Alter'),
                     ('das Bundesministerium der Finanzen', 'den Programmablaufplan zur Lohnsteuer des jeweiligen Jahres'),
                     ('das SGB III', 'die gesetzlichen Grundlagen zu Anwartschaft, Sperrzeit und Nebenverdienst')],
            fields=['das beitragspflichtige Bruttoentgelt der letzten zwölf Monate',
                    'Ihre Steuerklasse zum Stichtag', 'Ihr Alter und die Versicherungsmonate in der Rahmenfrist',
                    'ob ein Kind im Sinne des Leistungssatzes berücksichtigt wird'],
        )}},
    'fr-simulateur-are': {
        'langs': {'fr': dict(
            subject='l’allocation d’aide au retour à l’emploi (ARE)',
            authority='France Travail',
            official=('le simulateur officiel de France Travail', 'https://www.francetravail.fr/'),
            regulator='la CNIL',
            law='le RGPD et la loi Informatique et Libertés',
            sources=[('l’Unédic', 'la convention d’assurance chômage, les coefficients et les planchers de l’ARE'),
                     ('France Travail', 'les paramètres annuels revalorisés et les règles de cumul'),
                     ('l’URSSAF et le Code de la sécurité sociale', 'les taux de CSG et de CRDS et les seuils d’exonération')],
            fields=['votre salaire journalier de référence ou vos salaires bruts sur la période de référence',
                    'la durée d’affiliation en jours travaillés', 'votre âge à la fin du contrat de travail',
                    'le revenu fiscal de référence utilisé pour le taux de CSG'],
        )}},
    'es-calculadora-paro': {
        'langs': {'es': dict(
            subject='la prestación por desempleo',
            authority='el SEPE',
            official=('el autocálculo del SEPE', 'https://www.sepe.es/'),
            regulator='la Agencia Española de Protección de Datos',
            law='el RGPD y la LOPDGDD',
            sources=[('el SEPE', 'las cuantías máximas y mínimas, los topes del IPREM y la duración según lo cotizado'),
                     ('la Seguridad Social', 'las bases de cotización y el tipo de cotización a cargo del beneficiario'),
                     ('la Agencia Tributaria', 'los tipos de retención de IRPF y los límites de la obligación de declarar')],
            fields=['las bases de cotización de los últimos 180 días',
                    'los días cotizados en los últimos seis años', 'el número de hijos a cargo',
                    'si ha solicitado una retención de IRPF voluntaria'],
        )}},
}

# --------------------------------------------------------------------------- #
# Libellés d'interface par langue
# --------------------------------------------------------------------------- #
L = {
 'en': dict(contact='Contact', editorial='Editorial and corrections policy', cookies='Cookies',
            bc_contact='Contact', bc_editorial='Editorial policy', bc_cookies='Cookies'),
 'fr': dict(contact='Contact', editorial='Charte éditoriale et politique de correction', cookies='Cookies',
            bc_contact='Contact', bc_editorial='Charte éditoriale', bc_cookies='Cookies'),
 'nl': dict(contact='Contact', editorial='Redactiestatuut en correctiebeleid', cookies='Cookies',
            bc_contact='Contact', bc_editorial='Redactie en correcties', bc_cookies='Cookies'),
 'de': dict(contact='Kontakt', editorial='Redaktions- und Korrekturrichtlinie', cookies='Cookie-Hinweis',
            bc_contact='Kontakt', bc_editorial='Redaktion & Korrekturen', bc_cookies='Cookies'),
 'es': dict(contact='Contacto', editorial='Política editorial y de correcciones', cookies='Cookies',
            bc_contact='Contacto', bc_editorial='Política editorial', bc_cookies='Cookies'),
}

CONTACT = {
 'en': """    <h1>Contact</h1>
    <p>We read every message. Write to <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>.</p>

    <h2>Reporting a calculation error</h2>
    <p>This is the most useful feedback we can get. To reproduce a case we need four things:</p>
    <ol>
      <li>the <strong>share link</strong> produced by the calculator, which encodes every input in the URL — or failing that, {fields};</li>
      <li>the figure you expected;</li>
      <li>where that figure comes from, ideally <a href="{official_url}" rel="noopener" target="_blank">{official_name}</a>, a decision letter or a payslip;</li>
      <li>the year concerned.</li>
    </ol>
    <p>Any confirmed discrepancy above one per cent is treated as a defect: we fix the data, extend the reference cases so the same error cannot return, and record the correction in our <a href={{route('editorial', lang)}}>editorial policy</a>. What the tool does and deliberately does not cover is set out in the <a href={{route('method', lang)}}>methodology</a>.</p>

    <h2>Press and newsrooms</h2>
    <p>We produce extracts from our dataset on request, as CSV where that helps — distributions, thresholds and year-on-year changes. Please tell us the outlet, the topic and your deadline.</p>

    <h2>Embedding the calculator</h2>
    <p>The calculator can be embedded free of charge in an iframe on your own site, which HR teams, employment lawyers and advice services do regularly. Ask us and we will send the embed code and the terms of use.</p>

    <h2>What we do not do</h2>
    <p>We give <strong>no individual legal, tax or financial advice</strong> and cannot review a claim or a decision. Questions about your own entitlement belong with {authority}, or with a qualified adviser. We cannot intervene in a decision, appeal on your behalf, or tell you what {authority} will decide.</p>

    <h2>Response times</h2>
    <p>We normally reply within five working days, and prioritise reports of calculation errors. Independently of that, every dataset is reviewed at least every {{REVIEW_CYCLE_MONTHS}} months.</p>

    <h2>Publisher</h2>
    <LegalIdentity lang={lang} />
    <p>Full details in our <a href={{route('terms', lang)}}>terms and legal notice</a>. Responsible for content: {{AUTHOR_NAME}}. Last updated: {{LAST_UPDATED}}.</p>""",

 'fr': """    <h1>Contact</h1>
    <p>Nous lisons chaque message. Écrivez à <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>.</p>

    <h2>Signaler une erreur de calcul</h2>
    <p>C’est le retour le plus utile que nous puissions recevoir. Pour reproduire un cas, il nous faut quatre éléments :</p>
    <ol>
      <li>le <strong>lien de partage</strong> généré par le calculateur, qui encode toutes vos saisies dans l’URL – ou, à défaut, {fields} ;</li>
      <li>la valeur que vous attendiez ;</li>
      <li>la source de cette valeur, idéalement <a href="{official_url}" rel="noopener" target="_blank">{official_name}</a>, une notification de décision ou un bulletin de salaire ;</li>
      <li>l’année concernée.</li>
    </ol>
    <p>Tout écart confirmé supérieur à un pour cent est traité comme un défaut : nous corrigeons les données, étendons les cas de référence pour que la même erreur ne revienne pas, et consignons la correction dans notre <a href={{route('editorial', lang)}}>charte éditoriale</a>. Ce que l’outil couvre et ce qu’il ne couvre volontairement pas figure dans la <a href={{route('method', lang)}}>méthodologie</a>.</p>

    <h2>Presse et rédactions</h2>
    <p>Nous produisons sur demande des extractions de notre base – répartitions, seuils, évolutions d’une année sur l’autre – au format CSV lorsque c’est utile. Merci d’indiquer le média, le sujet et votre échéance.</p>

    <h2>Intégrer le calculateur</h2>
    <p>Le calculateur s’intègre gratuitement en iframe sur votre site, ce que font régulièrement des services RH, des avocats en droit du travail et des structures d’accompagnement. Demandez-nous le code d’intégration et les conditions d’utilisation.</p>

    <h2>Ce que nous ne faisons pas</h2>
    <p>Nous ne donnons <strong>aucun conseil juridique, fiscal ou financier individuel</strong> et ne pouvons examiner ni un dossier ni une décision. Les questions portant sur vos propres droits relèvent de {authority} ou d’un professionnel qualifié. Nous ne pouvons pas intervenir dans une décision, exercer un recours à votre place, ni vous dire ce que {authority} décidera.</p>

    <h2>Délais de réponse</h2>
    <p>Nous répondons en général sous cinq jours ouvrés et traitons en priorité les signalements d’erreur de calcul. Indépendamment de cela, chaque jeu de données est revu au moins tous les {{REVIEW_CYCLE_MONTHS}} mois.</p>

    <h2>Éditeur</h2>
    <LegalIdentity lang={lang} />
    <p>Informations complètes dans nos <a href={{route('terms', lang)}}>mentions légales</a>. Responsable du contenu : {{AUTHOR_NAME}}. Dernière mise à jour : {{LAST_UPDATED}}.</p>""",

 'nl': """    <h1>Contact</h1>
    <p>We lezen elk bericht. Schrijf naar <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>.</p>

    <h2>Een rekenfout melden</h2>
    <p>Dat is de nuttigste reactie die we kunnen krijgen. Om een geval na te rekenen hebben we vier dingen nodig:</p>
    <ol>
      <li>de <strong>deellink</strong> uit de rekenhulp, waarin alle invoer in de URL is gecodeerd – of anders {fields};</li>
      <li>het bedrag dat u verwachtte;</li>
      <li>waar dat bedrag vandaan komt, bij voorkeur <a href="{official_url}" rel="noopener" target="_blank">{official_name}</a>, een beslissing of een loonstrook;</li>
      <li>het jaar waarover het gaat.</li>
    </ol>
    <p>Elk bevestigd verschil van meer dan één procent behandelen we als een fout: we corrigeren de gegevens, breiden de referentiegevallen uit zodat dezelfde fout niet kan terugkeren, en leggen de correctie vast in ons <a href={{route('editorial', lang)}}>redactiestatuut</a>. Wat de rekenhulp wel en bewust niet doet, staat in de <a href={{route('method', lang)}}>methode en bronnen</a>.</p>

    <h2>Pers en redacties</h2>
    <p>Op verzoek maken we uitdraaien uit onze gegevens – verdelingen, drempels, verschillen van jaar tot jaar – desgewenst als CSV. Vermeld het medium, het onderwerp en uw deadline.</p>

    <h2>De rekenhulp insluiten</h2>
    <p>De rekenhulp kan gratis als iframe op uw eigen site worden geplaatst, wat HR-afdelingen, arbeidsrechtadvocaten en rechtshulpverleners geregeld doen. Vraag ons om de insluitcode en de gebruiksvoorwaarden.</p>

    <h2>Wat we niet doen</h2>
    <p>We geven <strong>geen individueel juridisch, fiscaal of financieel advies</strong> en kunnen geen dossier of beslissing beoordelen. Vragen over uw eigen recht horen thuis bij {authority} of bij een gekwalificeerde adviseur. We kunnen niet ingrijpen in een beslissing, namens u bezwaar maken, of zeggen wat {authority} zal besluiten.</p>

    <h2>Reactietermijn</h2>
    <p>We reageren doorgaans binnen vijf werkdagen en behandelen meldingen van rekenfouten met voorrang. Los daarvan wordt elke gegevensset ten minste elke {{REVIEW_CYCLE_MONTHS}} maanden herzien.</p>

    <h2>Uitgever</h2>
    <LegalIdentity lang={lang} />
    <p>Volledige gegevens in de <a href={{route('terms', lang)}}>disclaimer</a>. Verantwoordelijk voor de inhoud: {{AUTHOR_NAME}}. Bijgewerkt: {{LAST_UPDATED}}.</p>""",

 'de': """    <h1>Kontakt</h1>
    <p>Wir lesen jede Nachricht. Schreiben Sie an <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>.</p>

    <h2>Einen Rechenfehler melden</h2>
    <p>Das ist die nützlichste Rückmeldung, die wir bekommen können. Damit wir einen Fall nachvollziehen können, brauchen wir vier Angaben:</p>
    <ol>
      <li>den <strong>Teilen-Link</strong> aus dem Rechner, der alle Eingaben in der URL kodiert – ersatzweise {fields};</li>
      <li>den Wert, den Sie erwartet haben;</li>
      <li>die Quelle dieses Werts, idealerweise <a href="{official_url}" rel="noopener" target="_blank">{official_name}</a>, ein Bescheid oder eine Lohnabrechnung;</li>
      <li>das betroffene Jahr.</li>
    </ol>
    <p>Jede bestätigte Abweichung von mehr als einem Prozent behandeln wir als Fehler: Wir korrigieren die Daten, erweitern die Referenzfälle, damit derselbe Fehler nicht zurückkehrt, und halten die Korrektur in unserer <a href={{route('editorial', lang)}}>Redaktionsrichtlinie</a> fest. Was der Rechner leistet und was bewusst nicht, steht in der <a href={{route('method', lang)}}>Methodik</a>.</p>

    <h2>Presse und Redaktionen</h2>
    <p>Auf Anfrage erstellen wir Auswertungen aus unserem Datenbestand – Verteilungen, Schwellenwerte, Veränderungen im Jahresvergleich – bei Bedarf als CSV. Bitte nennen Sie Medium, Thema und Termin.</p>

    <h2>Den Rechner einbinden</h2>
    <p>Der Rechner lässt sich kostenlos als iframe auf Ihrer eigenen Website einbetten, was Personalabteilungen, Fachanwältinnen für Arbeitsrecht und Beratungsstellen regelmässig tun. Fragen Sie uns nach dem Einbettungscode und den Nutzungsbedingungen.</p>

    <h2>Was wir nicht anbieten</h2>
    <p>Wir erteilen <strong>keine individuelle Rechts-, Steuer- oder Finanzberatung</strong> und können weder einen Antrag noch einen Bescheid prüfen. Fragen zu Ihrem eigenen Anspruch beantwortet {authority} oder eine qualifizierte Beratung. Wir können nicht in ein Verfahren eingreifen, keinen Widerspruch für Sie einlegen und nicht vorhersagen, wie {authority} entscheiden wird.</p>

    <h2>Antwortzeiten</h2>
    <p>Wir antworten in der Regel innerhalb von fünf Arbeitstagen und ziehen Meldungen zu Rechenfehlern vor. Unabhängig davon wird jeder Datensatz mindestens alle {{REVIEW_CYCLE_MONTHS}} Monate überprüft.</p>

    <h2>Anbieter</h2>
    <LegalIdentity lang={lang} />
    <p>Vollständige Angaben im <a href={{route('terms', lang)}}>Impressum</a>. Verantwortlich für den Inhalt: {{AUTHOR_NAME}}. Stand: {{LAST_UPDATED}}.</p>""",

 'es': """    <h1>Contacto</h1>
    <p>Leemos todos los mensajes. Escríbanos a <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>.</p>

    <h2>Comunicar un error de cálculo</h2>
    <p>Es la aportación más útil que podemos recibir. Para reproducir un caso necesitamos cuatro datos:</p>
    <ol>
      <li>el <strong>enlace para compartir</strong> que genera la calculadora, que codifica todos los datos en la URL — o, en su defecto, {fields};</li>
      <li>el importe que usted esperaba;</li>
      <li>de dónde procede ese importe, preferiblemente <a href="{official_url}" rel="noopener" target="_blank">{official_name}</a>, una resolución o una nómina;</li>
      <li>el año al que se refiere.</li>
    </ol>
    <p>Toda discrepancia confirmada superior al uno por ciento se trata como un defecto: corregimos los datos, ampliamos los casos de referencia para que el mismo error no pueda repetirse y dejamos constancia de la corrección en nuestra <a href={{route('editorial', lang)}}>política editorial</a>. Lo que la herramienta hace y lo que deliberadamente no cubre figura en la <a href={{route('method', lang)}}>metodología</a>.</p>

    <h2>Prensa y redacciones</h2>
    <p>Bajo petición elaboramos extracciones de nuestros datos — distribuciones, umbrales, variaciones interanuales — en CSV cuando resulta útil. Indíquenos el medio, el tema y su plazo.</p>

    <h2>Integrar la calculadora</h2>
    <p>La calculadora puede integrarse gratuitamente mediante iframe en su propio sitio, algo que hacen con regularidad departamentos de recursos humanos, abogados laboralistas y servicios de orientación. Pídanos el código de integración y las condiciones de uso.</p>

    <h2>Lo que no hacemos</h2>
    <p>No prestamos <strong>asesoramiento jurídico, fiscal ni financiero individual</strong> y no podemos revisar un expediente ni una resolución. Las preguntas sobre su propio derecho corresponden a {authority} o a un profesional cualificado. No podemos intervenir en un procedimiento, recurrir en su nombre ni anticipar lo que {authority} resolverá.</p>

    <h2>Plazos de respuesta</h2>
    <p>Respondemos normalmente en cinco días hábiles y damos prioridad a los avisos de error de cálculo. Con independencia de ello, cada conjunto de datos se revisa al menos cada {{REVIEW_CYCLE_MONTHS}} meses.</p>

    <h2>Editor</h2>
    <LegalIdentity lang={lang} />
    <p>Datos completos en el <a href={{route('terms', lang)}}>aviso legal</a>. Responsable del contenido: {{AUTHOR_NAME}}. Última actualización: {{LAST_UPDATED}}.</p>""",
}

EDITORIAL = {
 'en': """    <h1>Editorial and corrections policy</h1>
    <p>This calculator deals with money people actually have to live on. So we set out where the figures come from, who is answerable for them, and what happens when one of them is wrong.</p>

    <h2>Who is responsible</h2>
    <p>Content and calculations are the responsibility of {{AUTHOR_NAME}}. There is no newsroom in the traditional sense: data preparation, writing and the calculation engine are the work of one person, which makes accountability unambiguous. For editorial questions: <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>.</p>

    <h2>Primary sources only</h2>
    <p>We take no figure from another calculator, a news article or an advice site. Every parameter comes from an official publication:</p>
    <ul>
{sources_html}
    </ul>
    <p>Every data file carries <code>source</code>, <code>source_url</code>, <code>retrieved_at</code>, <code>valid_from</code> and <code>valid_to</code> in its header. The full derivation is set out in the <a href={{route('method', lang)}}>methodology</a>.</p>

    <h2>Testing before publication</h2>
    <p>A set of reference cases runs against the engine on every build. If a case deviates beyond the agreed tolerance, the build fails and the version is never served. The threshold is deliberately tight: it separates acceptable rounding from a genuine error in the rules.</p>

    <h2>Update cycle</h2>
    <p>Every parameter is reviewed in full at least every {{REVIEW_CYCLE_MONTHS}} months, and whenever an authority publishes new figures. The visible “last updated” date on each page is not decoration: it is generated from the <code>retrieved_at</code> field of the underlying data file and moves only when the data moves.</p>

    <h2>How we handle errors</h2>
    <p>Reported discrepancies are checked against the primary source. Where the error is confirmed:</p>
    <ol>
      <li>The data or the code is fixed and the reference cases are extended so the same error cannot return.</li>
      <li>The affected page gets a new update date.</li>
      <li>Where the error materially affected a published result, the correction is noted on the page rather than substituted in silence.</li>
    </ol>
    <p>We do not delete pages to hide mistakes, and we do not publish a correction without saying what was wrong.</p>

    <h2>Independence and funding</h2>
    <p>The site carries no advertising and is funded by its publisher alone. No third party influences the calculation or the ordering of any result we publish. We sell no leads, refer no one to a lender, insurer or law firm, and accept no payment for a mention. If a relationship with a named organisation existed, it would be stated in the text.</p>

    <h2>What the calculator does not do</h2>
    <p>The result is an estimate based on the standard rules. It replaces neither a decision by {authority} nor individual professional advice. The limits are listed one by one in the <a href={{route('method', lang)}}>methodology</a>.</p>

    <p>Version of this policy: {{LAST_UPDATED}}.</p>""",

 'fr': """    <h1>Charte éditoriale et politique de correction</h1>
    <p>Ce calculateur parle d’argent dont les gens doivent réellement vivre. Nous exposons donc d’où viennent les chiffres, qui en répond, et ce qui se passe lorsque l’un d’eux est faux.</p>

    <h2>Responsabilité</h2>
    <p>Le contenu et les calculs sont sous la responsabilité de {{AUTHOR_NAME}}. Il n’y a pas de rédaction au sens classique : préparation des données, rédaction et moteur de calcul relèvent d’une seule personne, ce qui rend la responsabilité sans ambiguïté. Pour toute question de fond : <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>.</p>

    <h2>Sources primaires uniquement</h2>
    <p>Nous ne reprenons aucun chiffre d’un autre calculateur, d’un article de presse ou d’un site de conseils. Chaque paramètre provient d’une publication officielle :</p>
    <ul>
{sources_html}
    </ul>
    <p>Chaque fichier de données porte en en-tête les champs <code>source</code>, <code>source_url</code>, <code>retrieved_at</code>, <code>valid_from</code> et <code>valid_to</code>. Le détail du raisonnement figure dans la <a href={{route('method', lang)}}>méthodologie</a>.</p>

    <h2>Tests avant publication</h2>
    <p>Un jeu de cas de référence est exécuté contre le moteur à chaque compilation. Si un cas s’écarte au-delà de la tolérance retenue, la compilation échoue et la version n’est jamais mise en ligne. Ce seuil est volontairement serré : il distingue un écart d’arrondi acceptable d’une véritable erreur de règle.</p>

    <h2>Cycle de mise à jour</h2>
    <p>Chaque paramètre est revu intégralement au moins tous les {{REVIEW_CYCLE_MONTHS}} mois, et chaque fois qu’une administration publie de nouvelles valeurs. La date de mise à jour affichée sur chaque page n’est pas décorative : elle est générée à partir du champ <code>retrieved_at</code> du fichier de données sous-jacent et ne bouge que si les données bougent.</p>

    <h2>Traitement des erreurs</h2>
    <p>Tout écart signalé est vérifié contre la source primaire. S’il est confirmé :</p>
    <ol>
      <li>Les données ou le code sont corrigés et les cas de référence étendus, afin que la même erreur ne puisse pas revenir.</li>
      <li>La page concernée reçoit une nouvelle date de mise à jour.</li>
      <li>Si l’erreur affectait un résultat publié de façon substantielle, la correction est signalée sur la page plutôt que substituée en silence.</li>
    </ol>
    <p>Nous ne supprimons pas de page pour masquer une erreur et ne publions pas de correction sans dire ce qui était faux.</p>

    <h2>Indépendance et financement</h2>
    <p>Le site n’affiche aucune publicité et il est financé par son seul éditeur. Aucun tiers n’influe sur le calcul ni sur l’ordre des résultats que nous publions. Nous ne vendons aucun prospect, n’orientons personne vers un prêteur, un assureur ou un cabinet, et n’acceptons aucune rémunération pour une citation. S’il existait un lien avec un organisme mentionné, il serait indiqué dans le texte.</p>

    <h2>Ce que le calculateur ne fait pas</h2>
    <p>Le résultat est une estimation fondée sur les règles standard. Il ne remplace ni une décision de {authority}, ni un conseil professionnel individuel. Les limites sont énumérées une à une dans la <a href={{route('method', lang)}}>méthodologie</a>.</p>

    <p>Version de la présente charte : {{LAST_UPDATED}}.</p>""",

 'nl': """    <h1>Redactiestatuut en correctiebeleid</h1>
    <p>Deze rekenhulp gaat over geld waarvan mensen daadwerkelijk moeten leven. Daarom leggen we vast waar de cijfers vandaan komen, wie ervoor verantwoordelijk is, en wat er gebeurt als er één niet klopt.</p>

    <h2>Verantwoordelijkheid</h2>
    <p>De inhoud en de berekeningen vallen onder de verantwoordelijkheid van {{AUTHOR_NAME}}. Er is geen redactie in de klassieke zin: gegevensverwerking, tekst en rekenmotor komen van één persoon, wat de verantwoordelijkheid ondubbelzinnig maakt. Voor inhoudelijke vragen: <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>.</p>

    <h2>Uitsluitend primaire bronnen</h2>
    <p>We nemen geen cijfer over van een andere rekenhulp, een nieuwsbericht of een adviessite. Elke parameter komt uit een officiële publicatie:</p>
    <ul>
{sources_html}
    </ul>
    <p>Elk gegevensbestand draagt in de kop de velden <code>source</code>, <code>source_url</code>, <code>retrieved_at</code>, <code>valid_from</code> en <code>valid_to</code>. De volledige afleiding staat in <a href={{route('method', lang)}}>methode en bronnen</a>.</p>

    <h2>Toetsing vóór publicatie</h2>
    <p>Bij elke build draait een set referentiegevallen tegen de rekenmotor. Wijkt een geval verder af dan de aanvaarde marge, dan faalt de build en wordt de versie nooit uitgeleverd. Die drempel is bewust krap: hij scheidt een aanvaardbaar afrondingsverschil van een echte fout in de regels.</p>

    <h2>Actualiseringscyclus</h2>
    <p>Elke parameter wordt ten minste elke {{REVIEW_CYCLE_MONTHS}} maanden volledig herzien, en telkens wanneer een instantie nieuwe cijfers publiceert. De zichtbare datum «bijgewerkt» op elke pagina is geen decoratie: hij wordt gegenereerd uit het veld <code>retrieved_at</code> van het onderliggende gegevensbestand en verandert alleen als de gegevens veranderen.</p>

    <h2>Omgaan met fouten</h2>
    <p>Gemelde verschillen toetsen we aan de primaire bron. Wordt de fout bevestigd, dan geldt:</p>
    <ol>
      <li>De gegevens of de code worden gecorrigeerd en de referentiegevallen uitgebreid, zodat dezelfde fout niet kan terugkeren.</li>
      <li>De betrokken pagina krijgt een nieuwe bijwerkdatum.</li>
      <li>Raakte de fout een gepubliceerde uitkomst wezenlijk, dan wordt de correctie op de pagina vermeld in plaats van stilzwijgend vervangen.</li>
    </ol>
    <p>We verwijderen geen pagina’s om fouten te verbergen, en publiceren geen correctie zonder te zeggen wat er mis was.</p>

    <h2>Onafhankelijkheid en financiering</h2>
    <p>De site toont geen advertenties en wordt uitsluitend door de uitgever zelf bekostigd. Geen enkele derde heeft invloed op de berekening of op de volgorde van de resultaten die we publiceren. We verkopen geen leads, verwijzen niemand door naar een kredietverstrekker, verzekeraar of advocatenkantoor, en aanvaarden geen betaling voor een vermelding. Bestond er een band met een genoemde organisatie, dan zou dat in de tekst staan.</p>

    <h2>Wat de rekenhulp niet doet</h2>
    <p>De uitkomst is een schatting op basis van de standaardregels. Ze vervangt geen beslissing van {authority} en geen individueel professioneel advies. De beperkingen staan stuk voor stuk in <a href={{route('method', lang)}}>methode en bronnen</a>.</p>

    <p>Versie van dit statuut: {{LAST_UPDATED}}.</p>""",

 'de': """    <h1>Redaktions- und Korrekturrichtlinie</h1>
    <p>Dieser Rechner behandelt Geld, von dem Menschen tatsächlich leben müssen. Deshalb legen wir offen, woher die Zahlen stammen, wer sie verantwortet und was passiert, wenn eine davon falsch ist.</p>

    <h2>Verantwortung</h2>
    <p>Verantwortlich für Inhalt und Berechnungen ist {{AUTHOR_NAME}}. Es gibt keine Redaktion im klassischen Sinn: Datenaufbereitung, Text und Rechenkern stammen aus einer Hand, was die Zuständigkeit eindeutig macht. Für inhaltliche Rückfragen: <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>.</p>

    <h2>Nur Primärquellen</h2>
    <p>Wir übernehmen keine Zahl von einem anderen Rechner, aus einem Zeitungsartikel oder von einer Ratgeberseite. Jeder Parameter stammt aus einer amtlichen Publikation:</p>
    <ul>
{sources_html}
    </ul>
    <p>Jede Datendatei trägt im Kopf die Felder <code>source</code>, <code>source_url</code>, <code>retrieved_at</code>, <code>valid_from</code> und <code>valid_to</code>. Die vollständige Herleitung steht in der <a href={{route('method', lang)}}>Methodik</a>.</p>

    <h2>Prüfung vor der Veröffentlichung</h2>
    <p>Bei jedem Build läuft ein Satz Referenzfälle gegen den Rechenkern. Weicht ein Fall über die vereinbarte Toleranz hinaus ab, schlägt der Build fehl und die Version wird nie ausgeliefert. Diese Schwelle ist bewusst eng: Sie trennt eine zulässige Rundungsdifferenz von einem echten Fehler in den Regeln.</p>

    <h2>Aktualisierungszyklus</h2>
    <p>Jeder Parameter wird mindestens alle {{REVIEW_CYCLE_MONTHS}} Monate vollständig überprüft, zusätzlich immer dann, wenn eine Behörde neue Werte publiziert. Das sichtbare Standdatum auf jeder Seite ist kein Dekor: Es wird aus dem Feld <code>retrieved_at</code> der zugrunde liegenden Datendatei erzeugt und ändert sich nur, wenn die Daten sich ändern.</p>

    <h2>Umgang mit Fehlern</h2>
    <p>Gemeldete Abweichungen prüfen wir gegen die Primärquelle. Bestätigt sich der Fehler, gilt:</p>
    <ol>
      <li>Die Daten oder der Code werden korrigiert und die Referenzfälle erweitert, damit derselbe Fehler nicht zurückkehrt.</li>
      <li>Die betroffene Seite erhält ein aktualisiertes Standdatum.</li>
      <li>Betraf der Fehler ein veröffentlichtes Ergebnis wesentlich, wird die Korrektur auf der Seite vermerkt, statt sie stillschweigend zu ersetzen.</li>
    </ol>
    <p>Wir löschen keine Seiten, um Fehler zu verbergen, und veröffentlichen keine Korrektur ohne Angabe dessen, was falsch war.</p>

    <h2>Unabhängigkeit und Finanzierung</h2>
    <p>Die Website zeigt keine Werbung und wird allein vom Anbieter finanziert. Kein Dritter nimmt Einfluss auf die Berechnung oder auf die Reihenfolge der von uns veröffentlichten Ergebnisse. Wir verkaufen keine Leads, vermitteln niemanden an Kreditgeber, Versicherer oder Kanzleien und nehmen kein Geld für eine Erwähnung entgegen. Bestünde eine Verbindung zu einer genannten Stelle, stünde sie im Text.</p>

    <h2>Was der Rechner nicht leistet</h2>
    <p>Das Ergebnis ist eine Schätzung auf Basis der Standardregeln. Es ersetzt weder eine Entscheidung durch {authority} noch eine individuelle fachliche Beratung. Die Grenzen sind in der <a href={{route('method', lang)}}>Methodik</a> einzeln aufgeführt.</p>

    <p>Stand dieser Richtlinie: {{LAST_UPDATED}}.</p>""",

 'es': """    <h1>Política editorial y de correcciones</h1>
    <p>Esta calculadora trata de dinero con el que las personas tienen que vivir realmente. Por eso explicamos de dónde salen las cifras, quién responde de ellas y qué ocurre cuando una es incorrecta.</p>

    <h2>Responsabilidad</h2>
    <p>El contenido y los cálculos son responsabilidad de {{AUTHOR_NAME}}. No hay redacción en el sentido clásico: la preparación de los datos, la redacción y el motor de cálculo proceden de una sola persona, lo que hace inequívoca la responsabilidad. Para cuestiones de fondo: <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>.</p>

    <h2>Solo fuentes primarias</h2>
    <p>No tomamos ninguna cifra de otra calculadora, de un artículo de prensa o de una web de consejos. Cada parámetro procede de una publicación oficial:</p>
    <ul>
{sources_html}
    </ul>
    <p>Cada archivo de datos lleva en su cabecera los campos <code>source</code>, <code>source_url</code>, <code>retrieved_at</code>, <code>valid_from</code> y <code>valid_to</code>. El razonamiento completo figura en la <a href={{route('method', lang)}}>metodología</a>.</p>

    <h2>Comprobación antes de publicar</h2>
    <p>En cada compilación se ejecuta un conjunto de casos de referencia contra el motor. Si un caso se desvía más allá de la tolerancia admitida, la compilación falla y la versión nunca se publica. El umbral es deliberadamente estricto: separa una diferencia de redondeo aceptable de un error real en las reglas.</p>

    <h2>Ciclo de actualización</h2>
    <p>Cada parámetro se revisa íntegramente al menos cada {{REVIEW_CYCLE_MONTHS}} meses, y siempre que un organismo publica nuevas cifras. La fecha de actualización visible en cada página no es decorativa: se genera a partir del campo <code>retrieved_at</code> del archivo de datos subyacente y solo cambia si cambian los datos.</p>

    <h2>Tratamiento de los errores</h2>
    <p>Toda discrepancia comunicada se contrasta con la fuente primaria. Si se confirma:</p>
    <ol>
      <li>Se corrigen los datos o el código y se amplían los casos de referencia, para que el mismo error no pueda repetirse.</li>
      <li>La página afectada recibe una nueva fecha de actualización.</li>
      <li>Si el error afectaba de forma sustancial a un resultado publicado, la corrección se indica en la página en lugar de sustituirse en silencio.</li>
    </ol>
    <p>No borramos páginas para ocultar errores ni publicamos una corrección sin decir qué estaba mal.</p>

    <h2>Independencia y financiación</h2>
    <p>El sitio no muestra publicidad y lo financia únicamente su titular. Ningún tercero influye en el cálculo ni en el orden de los resultados que publicamos. No vendemos contactos, no derivamos a nadie a entidades de crédito, aseguradoras o despachos, y no aceptamos pago por una mención. Si existiera un vínculo con alguna entidad citada, constaría en el texto.</p>

    <h2>Lo que la calculadora no hace</h2>
    <p>El resultado es una estimación basada en las reglas estándar. No sustituye una resolución de {authority} ni el asesoramiento profesional individual. Los límites se enumeran uno a uno en la <a href={{route('method', lang)}}>metodología</a>.</p>

    <p>Versión de esta política: {{LAST_UPDATED}}.</p>""",
}

COOKIES = {
 'en': """    <h1>Cookies</h1>
    <p>This page explains what the site stores on your device and what it measures. It supplements the <a href={{route('privacy', lang)}}>privacy policy</a>.</p>

    <h2>No cookies at all</h2>
    <p>This site sets <strong>no cookies</strong> — none for analytics, none for advertising, none to remember a choice. There is no advertising on the site, no audience analytics, and the publisher records no personal information about you. Every calculation runs in your browser; your inputs are never sent to a server.</p>

    <h2>Stability checks with Microsoft Clarity, cookie-free</h2>
    <p>To spot what goes wrong — JavaScript errors, slow pages, clicks that have no effect — the site uses Microsoft Clarity in its cookieless mode. Before anything is collected, the site tells Clarity not to store anything on your device. Clarity then sets no cookie, gives each page view its own one-off identifier and does not link one visit to another. Page text and everything you type are masked (“Strict” masking), so Clarity receives only the layout of the page, clicks, scrolling, device and browser type, load times and errors.</p>
    <ul>
      <li><strong>Purpose:</strong> a technical, anonymous measure of the site’s stability, and nothing else.</li>
      <li><strong>Provider:</strong> Microsoft Ireland Operations Limited, One Microsoft Place, South County Business Park, Leopardstown, Dublin 18, Ireland. Data may be transferred to Microsoft Corporation in the United States under the EU–U.S. Data Privacy Framework and standard contractual clauses.</li>
      <li><strong>Retention at Microsoft:</strong> page recordings 30 days, aggregated data up to 13 months.</li>
    </ul>
    <p>Because nothing is stored on or read back from your device to follow you, there is nothing to accept or refuse when you arrive on the site.</p>

    <h2>Local storage</h2>
    <p>The calculator may keep your last selection in your browser’s <code>localStorage</code> so you do not have to enter it again. That data never leaves your device, is never sent to us, and disappears if you clear site data in your browser settings.</p>

    <h2>Opting out and contact</h2>
    <p>If you prefer the site not to be measured at all, block the domain <code>clarity.ms</code> in your browser or use a content blocker: everything keeps working as before. Questions about this page, or about your rights under the applicable law ({law}) and before {regulator}: <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>. Last updated: {{LAST_UPDATED}}.</p>""",

 'fr': """    <h1>Cookies</h1>
    <p>Cette page indique ce que le site enregistre sur votre appareil et ce qu’il mesure. Elle complète la <a href={{route('privacy', lang)}}>politique de confidentialité</a>.</p>

    <h2>Aucun cookie</h2>
    <p>Ce site ne dépose <strong>aucun cookie</strong> : ni de mesure d’audience, ni publicitaire, ni même pour mémoriser un choix. Il n’affiche aucune publicité, n’utilise aucun outil d’analyse d’audience, et l’éditeur n’enregistre aucune donnée personnelle vous concernant. Les calculs s’exécutent dans votre navigateur ; vos saisies ne sont transmises à aucun serveur.</p>

    <h2>Mesure de la stabilité avec Microsoft Clarity, sans cookie</h2>
    <p>Pour détecter ce qui ne fonctionne pas – erreurs JavaScript, lenteurs, clics sans effet –, le site utilise Microsoft Clarity dans son mode sans cookie. Avant toute collecte, le site indique à Clarity de ne rien stocker sur votre appareil. Clarity ne dépose alors aucun cookie, attribue à chaque page vue un identifiant qui lui est propre et ne relie pas les visites entre elles. Le texte des pages et vos saisies sont masqués (masquage « strict ») : Clarity ne reçoit que la mise en page, les clics, le défilement, le type d’appareil et de navigateur, les temps de chargement et les erreurs.</p>
    <ul>
      <li><strong>Finalité :</strong> mesure technique et anonyme de la stabilité du site, à l’exclusion de tout autre usage.</li>
      <li><strong>Prestataire :</strong> Microsoft Ireland Operations Limited, One Microsoft Place, South County Business Park, Leopardstown, Dublin 18 (Irlande). Un transfert vers Microsoft Corporation aux États-Unis est possible, encadré par l’EU–U.S. Data Privacy Framework et des clauses contractuelles types.</li>
      <li><strong>Conservation chez Microsoft :</strong> enregistrements de pages 30 jours, données agrégées jusqu’à 13 mois.</li>
    </ul>
    <p>Rien n’étant déposé ni relu sur votre appareil pour vous suivre, vous n’avez rien à accepter ni à refuser en arrivant sur le site.</p>

    <h2>Stockage local</h2>
    <p>Le calculateur peut conserver votre dernière sélection dans le <code>localStorage</code> de votre navigateur, pour vous éviter de la ressaisir. Ces données ne quittent pas votre appareil, ne nous sont jamais envoyées et disparaissent si vous effacez les données de site dans les réglages de votre navigateur.</p>

    <h2>S’opposer à la mesure et nous écrire</h2>
    <p>Si vous préférez qu’aucune mesure n’ait lieu, bloquez le domaine <code>clarity.ms</code> dans votre navigateur ou utilisez un bloqueur de contenu : le site continue de fonctionner normalement. Pour toute question sur cette page ou sur vos droits au regard du cadre applicable ({law}) et devant {regulator} : <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>. Dernière mise à jour : {{LAST_UPDATED}}.</p>""",

 'nl': """    <h1>Cookies</h1>
    <p>Deze pagina legt uit wat de site op uw apparaat bewaart en wat hij meet. Ze vult de <a href={{route('privacy', lang)}}>privacyverklaring</a> aan.</p>

    <h2>Helemaal geen cookies</h2>
    <p>Deze site plaatst <strong>geen enkele cookie</strong>: geen statistiekcookies, geen advertentiecookies en ook geen cookie om een keuze te onthouden. Er staan geen advertenties op de site, er draaien geen bezoekstatistieken, en de uitgever slaat geen persoonsgegevens van u op. Alle berekeningen gebeuren in uw browser; uw invoer gaat naar geen enkele server.</p>

    <h2>Stabiliteitsmeting met Microsoft Clarity, zonder cookies</h2>
    <p>Om te zien wat er misgaat – JavaScript-fouten, trage pagina’s, klikken die niets doen – gebruikt de site Microsoft Clarity in de modus zonder cookies. Nog voordat er iets wordt verzameld, vraagt de site Clarity om niets op uw apparaat op te slaan. Clarity plaatst dan geen cookie, geeft elke paginaweergave een eigen kenmerk en koppelt bezoeken niet aan elkaar. Paginateksten en alles wat u invult worden afgeschermd (maskering ‘Strict’): Clarity krijgt alleen de opbouw van de pagina, klikken, scrollen, het type apparaat en browser, laadtijden en fouten te zien.</p>
    <ul>
      <li><strong>Doel:</strong> een technische en anonieme meting van de stabiliteit van de site, en verder niets.</li>
      <li><strong>Leverancier:</strong> Microsoft Ireland Operations Limited, One Microsoft Place, South County Business Park, Leopardstown, Dublin 18, Ierland. Doorgifte aan Microsoft Corporation in de Verenigde Staten is mogelijk, op basis van het EU–U.S. Data Privacy Framework en modelcontractbepalingen.</li>
      <li><strong>Bewaartermijn bij Microsoft:</strong> pagina-opnames 30 dagen, samengevoegde gegevens tot 13 maanden.</li>
    </ul>
    <p>Omdat er niets op uw apparaat wordt opgeslagen of uitgelezen om u te volgen, hoeft u bij binnenkomst niets te accepteren of te weigeren.</p>

    <h2>Lokale opslag</h2>
    <p>De rekenhulp kan uw laatste keuze bewaren in de <code>localStorage</code> van uw browser, zodat u die niet opnieuw hoeft in te voeren. Die gegevens verlaten uw apparaat niet, worden nooit naar ons gestuurd en verdwijnen zodra u de sitegegevens in uw browserinstellingen wist.</p>

    <h2>Bezwaar en contact</h2>
    <p>Wilt u helemaal niet gemeten worden, blokkeer dan het domein <code>clarity.ms</code> in uw browser of gebruik een contentblocker: de site blijft gewoon werken. Vragen over deze pagina, of over uw rechten onder het toepasselijke kader ({law}) en bij {regulator}: <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>. Bijgewerkt: {{LAST_UPDATED}}.</p>""",

 'de': """    <h1>Cookie-Hinweis</h1>
    <p>Diese Seite erklärt, was die Website auf Ihrem Gerät ablegt und was sie misst. Sie ergänzt die <a href={{route('privacy', lang)}}>Datenschutzerklärung</a>.</p>

    <h2>Überhaupt keine Cookies</h2>
    <p>Diese Website setzt <strong>keine Cookies</strong> – weder für Statistik noch für Werbung, nicht einmal, um eine Auswahl zu speichern. Es gibt keine Werbung, keine Reichweitenanalyse, und der Anbieter speichert keine personenbezogenen Daten über Sie. Alle Berechnungen laufen in Ihrem Browser; Ihre Eingaben gehen an keinen Server.</p>

    <h2>Stabilitätsmessung mit Microsoft Clarity, ohne Cookies</h2>
    <p>Um Störungen zu erkennen – JavaScript-Fehler, langsame Seiten, Klicks ohne Wirkung –, nutzt die Website Microsoft Clarity im cookielosen Modus. Bevor irgendetwas erfasst wird, weist die Website Clarity an, nichts auf Ihrem Gerät zu speichern. Clarity setzt daraufhin kein Cookie, vergibt für jeden Seitenaufruf eine eigene Kennung und verknüpft Besuche nicht miteinander. Seitentexte und alle Eingaben werden ausgeblendet (Maskierung „Strict“): Clarity erhält lediglich Seitenaufbau, Klicks, Scrollbewegungen, Geräte- und Browsertyp, Ladezeiten und Fehler.</p>
    <ul>
      <li><strong>Zweck:</strong> technische, anonyme Messung der Stabilität der Website – zu keinem anderen Zweck.</li>
      <li><strong>Anbieter:</strong> Microsoft Ireland Operations Limited, One Microsoft Place, South County Business Park, Leopardstown, Dublin 18, Irland. Eine Übermittlung an die Microsoft Corporation in den USA ist möglich; sie stützt sich auf das EU-US Data Privacy Framework und Standardvertragsklauseln.</li>
      <li><strong>Speicherdauer bei Microsoft:</strong> Seitenaufzeichnungen 30 Tage, zusammengefasste Daten bis zu 13 Monate.</li>
    </ul>
    <p>Da auf Ihrem Gerät nichts gespeichert und nichts zum Wiedererkennen ausgelesen wird, müssen Sie beim Aufruf der Website weder etwas annehmen noch ablehnen.</p>

    <h2>Lokale Speicherung</h2>
    <p>Der Rechner kann Ihre letzte Auswahl im <code>localStorage</code> Ihres Browsers ablegen, damit Sie sie nicht erneut eingeben müssen. Diese Daten verlassen Ihr Gerät nicht, werden nie an uns übertragen und lassen sich löschen, indem Sie die Websitedaten in Ihren Browsereinstellungen entfernen.</p>

    <h2>Widerspruch und Kontakt</h2>
    <p>Möchten Sie gar nicht gemessen werden, sperren Sie die Domain <code>clarity.ms</code> in Ihrem Browser oder verwenden Sie einen Inhaltsblocker – die Website funktioniert weiterhin uneingeschränkt. Fragen zu dieser Seite oder zu Ihren Rechten nach dem geltenden Recht ({law}) – Aufsichtsbehörde: {regulator} – richten Sie an <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>. Stand: {{LAST_UPDATED}}.</p>""",

 'es': """    <h1>Cookies</h1>
    <p>Esta página explica qué guarda el sitio en su dispositivo y qué mide. Complementa la <a href={{route('privacy', lang)}}>política de privacidad</a>.</p>

    <h2>Ninguna cookie</h2>
    <p>Este sitio <strong>no instala ninguna cookie</strong>: ni de medición, ni publicitaria, ni siquiera para recordar una elección. No muestra publicidad, no utiliza analítica de audiencia y el titular no registra ningún dato personal suyo. Los cálculos se hacen en su navegador; sus datos no se envían a ningún servidor.</p>

    <h2>Medición de la estabilidad con Microsoft Clarity, sin cookies</h2>
    <p>Para localizar fallos —errores de JavaScript, páginas lentas, clics que no hacen nada— el sitio utiliza Microsoft Clarity en su modo sin cookies. Antes de recoger cualquier dato, el sitio indica a Clarity que no almacene nada en su dispositivo. Clarity no instala entonces ninguna cookie, asigna a cada página vista un identificador propio y no vincula unas visitas con otras. Los textos y todo lo que usted escribe quedan ocultos (enmascaramiento «estricto»): Clarity solo recibe la disposición de la página, los clics, el desplazamiento, el tipo de dispositivo y de navegador, los tiempos de carga y los errores.</p>
    <ul>
      <li><strong>Finalidad:</strong> medición técnica y anónima de la estabilidad del sitio, sin ningún otro uso.</li>
      <li><strong>Proveedor:</strong> Microsoft Ireland Operations Limited, One Microsoft Place, South County Business Park, Leopardstown, Dublín 18 (Irlanda). Puede haber una transferencia a Microsoft Corporation en Estados Unidos, amparada en el EU–U.S. Data Privacy Framework y en cláusulas contractuales tipo.</li>
      <li><strong>Conservación en Microsoft:</strong> grabaciones de páginas 30 días, datos agregados hasta 13 meses.</li>
    </ul>
    <p>Como no se guarda ni se lee nada en su dispositivo para seguirle, no tiene nada que aceptar ni rechazar al entrar en el sitio.</p>

    <h2>Almacenamiento local</h2>
    <p>La calculadora puede conservar su última selección en el <code>localStorage</code> del navegador para que no tenga que volver a introducirla. Esos datos no salen de su dispositivo, nunca se nos envían y desaparecen si borra los datos del sitio en la configuración del navegador.</p>

    <h2>Oposición y contacto</h2>
    <p>Si prefiere que no se mida nada, bloquee el dominio <code>clarity.ms</code> en su navegador o use un bloqueador de contenidos: el sitio sigue funcionando con normalidad. Para cualquier duda sobre esta página o sobre sus derechos conforme a la normativa aplicable ({law}) y ante {regulator}: <a href={{`mailto:${{CONTACT_EMAIL}}`}}>{{CONTACT_EMAIL}}</a>. Última actualización: {{LAST_UPDATED}}.</p>""",
}

# --------------------------------------------------------------------------- #
# Métadonnées de page (title / description) par langue et par type
# --------------------------------------------------------------------------- #
META = {
 'en': {'contact': ('Contact – {site}', 'How to reach us: questions about the calculator, reporting a figure that looks wrong, press enquiries and embedding the tool on your own site.'),
        'editorial': ('Editorial and corrections policy – {site}', 'Where our figures come from, who answers for them, how often they are checked, and exactly what we do when a reader reports an error.'),
        'cookies': ('Cookies – {site}', 'This site sets no cookies. The only measurement is a cookieless, anonymous stability check with Microsoft Clarity, which you can block.')},
 'fr': {'contact': ('Contact – {site}', 'Comment nous joindre : questions sur le calculateur, signalement d’un montant qui paraît faux, demandes presse et intégration de l’outil sur votre site.'),
        'editorial': ('Charte éditoriale et corrections – {site}', 'D’où viennent nos chiffres, qui en répond, à quelle fréquence ils sont vérifiés, et ce que nous faisons exactement lorsqu’une erreur est signalée.'),
        'cookies': ('Cookies – {site}', 'Ce site ne dépose aucun cookie. Seule mesure : la stabilité du site, anonyme et sans cookie, avec Microsoft Clarity, que vous pouvez bloquer.')},
 'nl': {'contact': ('Contact – {site}', 'Hoe u ons bereikt: vragen over de rekenhulp, een bedrag melden dat niet lijkt te kloppen, persvragen en de tool op uw eigen site insluiten.'),
        'editorial': ('Redactiestatuut en correcties – {site}', 'Waar onze cijfers vandaan komen, wie ervoor verantwoordelijk is, hoe vaak ze worden getoetst en wat we doen als iemand een fout meldt.'),
        'cookies': ('Cookies – {site}', 'Deze site plaatst geen cookies. We meten alleen de stabiliteit, anoniem en zonder cookies, met Microsoft Clarity, en u kunt dat blokkeren.')},
 'de': {'contact': ('Kontakt – {site}', 'So erreichen Sie uns: Fragen zum Rechner, Meldung eines Betrags, der falsch wirkt, Presseanfragen und Einbindung des Rechners auf Ihrer Website.'),
        'editorial': ('Redaktion und Korrekturen – {site}', 'Woher unsere Zahlen stammen, wer sie verantwortet, wie oft sie geprüft werden und was genau geschieht, wenn jemand einen Fehler meldet.'),
        'cookies': ('Cookie-Hinweis – {site}', 'Diese Website setzt keine Cookies. Gemessen wird nur die Stabilität, anonym und cookielos mit Microsoft Clarity, was Sie blockieren können.')},
 'es': {'contact': ('Contacto – {site}', 'Cómo contactarnos: dudas sobre la calculadora, avisar de un importe que parece incorrecto, prensa e integración de la herramienta en su web.'),
        'editorial': ('Política editorial y correcciones – {site}', 'De dónde salen nuestras cifras, quién responde de ellas, con qué frecuencia se revisan y qué hacemos exactamente cuando alguien avisa de un error.'),
        'cookies': ('Cookies – {site}', 'Este sitio no instala cookies. Solo mide su estabilidad, de forma anónima y sin cookies, con Microsoft Clarity, algo que usted puede bloquear.')},
}

SRC_INTRO = {'en': 'for', 'fr': 'pour', 'nl': 'voor', 'de': 'für', 'es': 'para'}

SITE_NAME_EXPR = "SITE_NAMES[lang]"


def render(site, lang, kind, cfg, routes_path):
    body_tpl = {'contact': CONTACT, 'editorial': EDITORIAL, 'cookies': COOKIES}[kind][lang]
    fields = cfg['fields']
    fields_str = ', '.join(fields[:-1]) + (' and ' if lang == 'en' else
                  ' et ' if lang == 'fr' else ' en ' if lang == 'nl' else
                  ' und ' if lang == 'de' else ' y ') + fields[-1]
    src_html = '\n'.join(
        f"      <li><strong>{n}</strong> {SRC_INTRO[lang]} {d}.</li>" for n, d in cfg['sources'])
    body = body_tpl.format(fields=fields_str, authority=cfg['authority'],
                           official_name=cfg['official'][0], official_url=cfg['official'][1],
                           regulator=cfg['regulator'], law=cfg['law'], sources_html=src_html,
                           lang='{lang}')   # <LegalIdentity lang={lang} /> doit rester tel quel

    title_tpl, desc = META[lang][kind]
    depth = routes_path.strip('/').count('/') + 1          # /en/contact/ -> 1 segment de dossier
    up = '../' * depth
    needs_legal = kind == 'contact'
    imports = [f"import PageLayout from '{up}layouts/PageLayout.astro';"]
    if needs_legal:
        imports.append(f"import LegalIdentity from '{up}components/LegalIdentity.astro';")
    names = ['CONTACT_EMAIL', 'LAST_UPDATED', 'SITE_NAMES']
    if kind in ('contact', 'editorial'):
        names += ['AUTHOR_NAME', 'REVIEW_CYCLE_MONTHS']
    imports.append(f"import {{ {', '.join(sorted(set(names)))} }} from '{up}data/site-config';")
    imports.append(f"import {{ route }} from '{up}i18n/routes';")

    bc = L[lang][f'bc_{kind}']
    return (
        "---\n" + "\n".join(imports) + f"\nconst lang = '{lang}';\n"
        f"const title = `{title_tpl.replace('{site}', '${SITE_NAMES[lang]}')}`;\n"
        f"const description = '{desc.replace(chr(39), chr(92)+chr(39))}';\n---\n"
        f"<PageLayout title={{title}} description={{description}} lang={{lang}} noindex={{true}} "
        f"breadcrumbs={{[{{ label: '{bc}' }}]}} showAuthor={{false}}>\n"
        "  <div class=\"prose prose-slate max-w-none\">\n" + body + "\n  </div>\n</PageLayout>\n")


written = 0
for site, scfg in SITES.items():
    routes = open(os.path.join(ROOT, site, 'src/i18n/routes.ts'), encoding='utf-8').read()
    for lang, cfg in scfg['langs'].items():
        for kind in ('contact', 'editorial', 'cookies'):
            m = re.search(r"\{\s*id:\s*'" + kind + r"',\s*paths:\s*\{([^}]*)\}", routes)
            url = dict(re.findall(r"([a-z]{2}):\s*'([^']*)'", m.group(1)))[lang]
            rel = url.strip('/') + '.astro'
            dest = os.path.join(ROOT, site, 'src/pages', rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, 'w', encoding='utf-8').write(render(site, lang, kind, cfg, url))
            written += 1
            print(f'  {site}{url}')
print(f'{written} pages écrites')
