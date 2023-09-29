# Ideas

## Oraganizace písní

- každá písnička v samostaném souboru, včetně hlavičky (zatím ponechat, úprava formátu hlavičky případně později - zdroje, autoři)
- písničky v podadresářích hlavního adresáře `songs`, umožňuje i duplicitní verze písní, např. mohou být podadresáře podle toho,
  kdo vytvořil zdroják písně

## Docekerfile 
- Pro spouštění systému bude vyroben Dockerfile a na DockerHub nahrát vytvořený image.
- entrypoint bude volání hlavního Python skript (protože make file nemá argumenty)
- první argument hlavního `tragix.py` skriptu bude příkaz.

## tragix.py - příkazy
- `song_list <folders>` - vypíše všechny písně (reletivní cesta vůči `songs`) v zadaných adresářích do souboru `song_list`.
   Písně vypíše setříděné podle názvu písně, nehledě na název souboru a adresáře.

  Následně si uživatel může soubor `song_list` ručně upravit před jeho zpracováním příkazem `compile`

- `assembly` - sestaví ze souborů `header.tex`, `song_list` a `tail.tex` soubor `songbook.tex`
-  `compile`
   1. zavolá TeX kompilaci `songbook.tex` (kompletního zdrojáku zpěvníku) do `songbook.ps` ( případně PS pokud by byl problém)
   2. volá pstops  a následně pstopdf pro tvorbu `songbook-duplex.pdf`, `songbook-front.pdf`, `songbook-back.pdf` 

## todo:
- sjednotit ostatní todo
- update `Jak psat zpevnik` a oddělit jasně "Jak psát písně" a "Jak sestavit zpěvník"
