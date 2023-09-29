# Dokumentace systému

Retrospektivní dokumentace jak to asi fungovalo v roce 2007.

1. zbožnej a nezbožnej používají setejný hlavní makro soubor `lyric.tex`
   stejný je i soubor s diagramy akordů `chdig`
   
2. Hlavním vstupním bodem pro volání překladu zpěvníku je `makefile`, který je také v obou verzích 
   prakticky stejný. `zboznej` ma v tragetu `zpevnik.dvi` navíc `touch zpevnik.toc`
   
   Struktura `makefile`:
   
   1. příprava hlavního zdrojáku `zpevnik.tex` vstupem je `zpevnik.src`

      - **target convert** - provede konverzi do kódování il2
      - **target separate** - pomocí PERL makra `bin/sepsongs` se vstupní soubor s texty písniček rozkouskuje na písničky v samostatných souborech
      - **target sort** - setřídí písničky podle abecedy a opět vyrobí `zpevnik.src`
      
      Toto se evidentně volalo jen jednou a různě se to zakomentávávalo v makefile
   
      Nakonec se sestaví `zpevnik.tex` z titulní strany `zpevnik.head.tex`, volání formátovacích maker `\inputsong` pro jednotlivé písničky,
      a konce zpěvníku `zpevnik.tail.tex`.Pořadí písniček je dáno tím jak to vypisuje `ls songs/*.sng` takže `target sort` je asi zbytečný.  
   
   2. překlad `zpevnik.dvi`
      Používá si čistý TeX s formátem csplain. 
      Makro `\inputsong` upravuje tokenizér TeXu tak, že lze písničky zapisovat v čistém textu s minimem speciálního formátování.
      Syntaxe je popsaná v `JakPsatZpevnik-utf8.txt` 
   
