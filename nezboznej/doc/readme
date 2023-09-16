Posledni verze maker je v songs/all/lyric.tex
umi:
  - parsovat zacatky slok a to typu:
    R:, R1:, R2: ... refreny
    1:, 2: ...  normalni sloky
    C: ... recitativy, vypise se Rec:
    M: ... mezizpev, sazi se k levamu okraji
  - parsovat akordy, viz lyric.tex
  - do textu je mozno vpisovat jednoduche texovske sekvence jako vselijake
    \hskip, slozitejsi veci mohou mit nepredvidatelny nasledek
  - akord se umistuje na text ktery nasleduje az do dalsiho akordu nebo knce
    radku, pokud je text dost kratky ale dobre natazitelny tak se natahne
    a uzavre do boxy, kdyz je kratky a nenatahnutelny tak se provede deleni
    natahne se a da do boxu, jinak se necha tet volny, takze spravne funguji
    \hskip-y 
  - kazda pisnicka je uzavrena do boxu, a delka stranky je nastavena na
    dvojnasobek, tim se zaruci, ze pisnicka nebude pres list, ale muze byt na
    protilehle strance.
  - vystupni rutina - rozebere boxy pisnicek, prochazi vsechna mozna mista
    rozlomeni na 2 strany a vybere tu nejlepsi, pritom scita badness sestaveni
    stran a penalty v danem miste.
  - penalty jsou velmi citlive !!

songs/all/makefile 
ma pravidla proi:

zpevnik.tex - setridi vsechny *.sng v adresari a udela z nich zpevnik.tex,
              ktery ma na zacatku zpevnik.head.tex a na konci zpevnik.tail.tex
zpevnik.dvi - csplain
zpevnik.ps  - dvips

zpev-duplex.ps - pomoci pstops seradi stranky z zpevnik.ps aby to slo tisknou oboustrane jako 
                 brozuru, bohuzel dela 2x tolik stranek nez se ma tisknout
zpev-front.ps - prvni pula obsahuje liche strany z zpev-duplex.ps
zpev-back.ps - prvni pulka obsahuje sude strany z zpev-duplex.ps

zpev-*.pdf - pdf verze predchoziho



  
