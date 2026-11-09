/**
 * Libellés des composants communs de la trame, par langue (testeurs naïfs du 2026-11-08,
 * RECETTE §15.8). Ils ne dépendent pas de `i18n/ui.ts` du site : un composant de la trame
 * recopié dans un site existant parle aussitôt la langue de la page. Langue inconnue → anglais.
 *
 * - `exemple` : mention posée sur le résultat d'un calculateur tant que le lecteur n'a modifié
 *   aucun champ. Sans elle, trois testeurs sur trois ont lu le résultat pré-rempli comme leur
 *   verdict (« je suis éligible ») alors qu'il venait des valeurs d'exemple (financecertcost.com).
 * - `exempleAide` : la suite de la mention, qui dit quoi faire.
 * - `faqAide` : aide posée au-dessus des questions repliées (« Touchez une question pour voir la réponse ») :
 *   plusieurs testeurs ne voyaient pas que les questions s'ouvraient (goldbycarat.co.uk, dumpfeesbystate.com).
 * - `plusDeReglages`, `actuellement` : repli des champs facultatifs d'un calculateur ; son titre montre la
 *   valeur actuelle de chaque champ caché (« Actuellement : âge 40 ans · … »), car elle change le résultat
 *   (calculobeca.com : « d'où sort ce seuil 2 ? »).
 * - `lireTout` : lien du résumé replié (Clamp.astro). « Read more » laissait croire qu'il ouvrait
 *   une autre page, « Read the rest of this summary » qu'il existait un résumé ailleurs
 *   (dumpfeesbystate.com, goldbycarat.co.uk).
 */
export interface LibellesTrame { exemple: string; exempleAide: string; lireTout: string; faqAide: string; plusDeReglages: string; actuellement: string }

export const LIBELLES_TRAME: Record<string, LibellesTrame> = {
  en: { exemple: 'Example, not your result yet', exempleAide: 'change a figure to see yours', lireTout: 'Show the whole paragraph', faqAide: 'Tap a question to see the answer.', plusDeReglages: 'More about your case (optional, already filled in)', actuellement: 'Now' },
  fr: { exemple: 'Exemple, pas encore votre résultat', exempleAide: 'modifiez un chiffre pour voir le vôtre', lireTout: 'Lire tout le paragraphe', faqAide: 'Touchez une question pour voir la réponse.', plusDeReglages: 'Plus de détails sur votre cas (facultatif, déjà remplis)', actuellement: 'Actuellement' },
  es: { exemple: 'Ejemplo, todavía no es su resultado', exempleAide: 'cambie una cifra para ver el suyo', lireTout: 'Leer todo el párrafo', faqAide: 'Toque una pregunta para ver la respuesta.', plusDeReglages: 'Más datos de su caso (opcional, ya rellenos)', actuellement: 'Ahora' },
  de: { exemple: 'Beispiel, noch nicht Ihr Ergebnis', exempleAide: 'ändern Sie eine Zahl, um Ihres zu sehen', lireTout: 'Ganzen Absatz lesen', faqAide: 'Tippen Sie auf eine Frage, um die Antwort zu sehen.', plusDeReglages: 'Mehr zu Ihrem Fall (freiwillig, schon ausgefüllt)', actuellement: 'Derzeit' },
  it: { exemple: 'Esempio, non ancora il suo risultato', exempleAide: 'cambi una cifra per vedere il suo', lireTout: 'Leggi tutto il paragrafo', faqAide: 'Tocchi una domanda per vedere la risposta.', plusDeReglages: 'Altri dati del suo caso (facoltativi, già compilati)', actuellement: 'Ora' },
  pt: { exemple: 'Exemplo, ainda não é o seu resultado', exempleAide: 'altere um valor para ver o seu', lireTout: 'Ler o parágrafo inteiro', faqAide: 'Toque numa pergunta para ver a resposta.', plusDeReglages: 'Mais dados do seu caso (opcional, já preenchidos)', actuellement: 'Agora' },
  nl: { exemple: 'Voorbeeld, nog niet uw resultaat', exempleAide: 'wijzig een getal om het uwe te zien', lireTout: 'Hele alinea lezen', faqAide: 'Tik op een vraag om het antwoord te zien.', plusDeReglages: 'Meer over uw situatie (optioneel, al ingevuld)', actuellement: 'Nu' },
  pl: { exemple: 'Przykład, to jeszcze nie Twój wynik', exempleAide: 'zmień liczbę, aby zobaczyć swój', lireTout: 'Pokaż cały akapit', faqAide: 'Dotknij pytania, aby zobaczyć odpowiedź.', plusDeReglages: 'Więcej o Twojej sytuacji (opcjonalnie, już wypełnione)', actuellement: 'Teraz' },
  sv: { exemple: 'Exempel, ännu inte ditt resultat', exempleAide: 'ändra en siffra för att se ditt', lireTout: 'Visa hela stycket', faqAide: 'Tryck på en fråga för att se svaret.', plusDeReglages: 'Mer om din situation (frivilligt, redan ifyllt)', actuellement: 'Nu' },
  da: { exemple: 'Eksempel, endnu ikke dit resultat', exempleAide: 'ændr et tal for at se dit', lireTout: 'Vis hele afsnittet', faqAide: 'Tryk på et spørgsmål for at se svaret.', plusDeReglages: 'Mere om din situation (valgfrit, allerede udfyldt)', actuellement: 'Nu' },
  nb: { exemple: 'Eksempel, ennå ikke ditt resultat', exempleAide: 'endre et tall for å se ditt', lireTout: 'Vis hele avsnittet', faqAide: 'Trykk på et spørsmål for å se svaret.', plusDeReglages: 'Mer om din situasjon (valgfritt, allerede fylt ut)', actuellement: 'Nå' },
  fi: { exemple: 'Esimerkki, ei vielä sinun tuloksesi', exempleAide: 'muuta lukua nähdäksesi omasi', lireTout: 'Näytä koko kappale', faqAide: 'Napauta kysymystä nähdäksesi vastauksen.', plusDeReglages: 'Lisää tilanteestasi (valinnainen, valmiiksi täytetty)', actuellement: 'Nyt' },
  tr: { exemple: 'Örnek, henüz sizin sonucunuz değil', exempleAide: 'kendi sonucunuz için bir rakamı değiştirin', lireTout: 'Paragrafın tamamını göster', faqAide: 'Cevabı görmek için bir soruya dokunun.', plusDeReglages: 'Durumunuz hakkında daha fazlası (isteğe bağlı, dolduruldu)', actuellement: 'Şu an' },
  id: { exemple: 'Contoh, belum hasil Anda', exempleAide: 'ubah angka untuk melihat hasil Anda', lireTout: 'Tampilkan seluruh paragraf', faqAide: 'Ketuk pertanyaan untuk melihat jawabannya.', plusDeReglages: 'Detail lain tentang Anda (opsional, sudah terisi)', actuellement: 'Saat ini' },
  el: { exemple: 'Παράδειγμα, όχι ακόμη το δικό σας αποτέλεσμα', exempleAide: 'αλλάξτε έναν αριθμό για να δείτε το δικό σας', lireTout: 'Εμφάνιση ολόκληρης της παραγράφου', faqAide: 'Πατήστε μια ερώτηση για να δείτε την απάντηση.', plusDeReglages: 'Περισσότερα για την περίπτωσή σας (προαιρετικά, ήδη συμπληρωμένα)', actuellement: 'Τώρα' },
};
// Variantes de code (« no » pour le norvégien, « fr-BE », « pt_BR ») ramenées à la langue.
const ALIAS: Record<string, string> = { no: 'nb', nn: 'nb' };

export function libellesTrame(lang?: string): LibellesTrame {
  const base = String(lang ?? 'en').toLowerCase().split(/[-_]/)[0];
  return LIBELLES_TRAME[ALIAS[base] ?? base] ?? LIBELLES_TRAME.en;
}

/** Vrai tant qu'aucun champ n'a été modifié par le lecteur : le résultat montré est l'exemple. */
export function resultatExemple(touched: Record<string, boolean> | undefined): boolean {
  return !touched || !Object.values(touched).some(Boolean);
}

/** Ligne « Actuellement : … » d'un repli : libellé et valeur affichée de chaque champ caché.
 *  Deux-points précédé d'une espace insécable en français seulement. */
export function resumeRepli(lang: string | undefined, champs: Array<{ label: string; valeur: string }>): string {
  const deuxPoints = /^fr\b/i.test(String(lang ?? '')) ? '\u00a0:' : ':';
  return `${libellesTrame(lang).actuellement}${deuxPoints} ${champs.map((c) => `${c.label} ${c.valeur}`).join(' · ')}`;
}
