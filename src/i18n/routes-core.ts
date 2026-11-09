/**
 * Fabrique des helpers de routage multi-locale à partir d'une table ROUTES.
 *
 * Une locale peut être partielle. Un site qui ouvre une deuxième langue ne
 * traduit pas ses quatre-vingts pages le même jour : la table accepte donc
 * qu'une route n'existe que dans certaines langues, et tout ce qui en découle
 * s'aligne — le hreflang ne pointe que vers des pages qui existent, le
 * sélecteur de langue ne propose que ce qui est traduit, et le sitemap
 * n'annonce rien d'absent.
 *
 * C'est aussi ce que demande Google : un `alternate` vers une page qui répond
 * 404 invalide tout le jeu d'annotations de la page, donc une traduction
 * partielle mal déclarée coûte plus cher que pas de traduction du tout.
 */
export interface RouteDef<L extends string> {
  id: string;
  /** Une entrée par langue où la page existe. Les autres sont absentes. */
  paths: Partial<Record<L, string>>;
  noindex?: boolean;
}

export function makeRouter<L extends string>(locales: readonly L[], routes: RouteDef<L>[]) {
  const NOINDEX_PATHS = routes
    .filter((r) => r.noindex)
    .flatMap((r) => locales.map((l) => r.paths[l]).filter((p): p is string => !!p));

  /** Le chemin d'une route dans une langue. Retombe sur la langue par défaut
   *  quand la page n'est pas traduite : un lien de navigation doit mener
   *  quelque part, et la version d'origine vaut mieux qu'une 404. */
  function route(id: string, lang: L): string {
    const r = routes.find((x) => x.id === id);
    if (!r) throw new Error(`Unknown route id: ${id}`);
    const p = r.paths[lang] ?? r.paths[locales[0]];
    if (!p) throw new Error(`Route ${id} has no path in any locale`);
    return p;
  }

  /** Vrai si la page existe réellement dans cette langue. */
  function hasRoute(id: string, lang: L): boolean {
    const r = routes.find((x) => x.id === id);
    return !!r && !!r.paths[lang];
  }

  /** Les traductions existantes d'un chemin, la langue courante comprise.
   *  Ne renvoie que ce qui existe : c'est ce qui alimente le hreflang. */
  function altPaths(pathname: string): Partial<Record<L, string>> | null {
    const r = routes.find((x) => locales.some((l) => x.paths[l] === pathname));
    return r ? r.paths : null;
  }

  return { NOINDEX_PATHS, route, hasRoute, altPaths };
}
