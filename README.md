# Zpěvníky oddílů Ichthys

TragIx = Tragoudi Ixtys = Zpívající Ryba

## Dokumentace systému

Retrospektivní dokumentace jak to asi fungovalo v roce 2007.

1. zbožnej a nezbožnej používají setejný hlavní makro soubor `lyric.tex`
   stejný je i soubor s diagramy akordů `chdig`
   
2. Hlavním vstupním bodem pro volání překladu zpěvníku je `makefile`, který je také v obou verzích 
   prakticky stejný. `zboznej` ma v tragetu `zpevnik.dvi` navíc `touch zpevnik.toc`
   
   Struktura:
   A. příprava hlavního zdrojáku zpevnik.tex
   vstupem je `zpevnik.src`
   target convert - provede konverzi do kódování il2
   target separate - pomocí PERL makra `bin/sepsongs` se vstupní soubor s texty písniček rozkouskuje na písničky v samostatných souborech
   target sort - setřídí písničky podle abecedy a opět vyrobí `zpevnik.src`
   Toto se evidentně volalo jen jednou a různě se to zakomentávávalo v makefile
   
   Nakonec se sestaví `zpevnik.tex` z titulní strany `zpevnik.head.tex`, volání formátovacích maker pro jednotlivé písničky, a konce zpěvníku `zpevnik.tail.tex`
   Pořadí písniček je dáno tím jak to vypisuje `ls songs/*.sng` takže target sort je asi zbytečný.  
   
   Takto vytvořený zpevnik.tex se dále ručně upravoval, aby se dobře využilo místo.
   
   B. překlad `zpevnik.dvi`
   Používá si čistý TeX s formátem csplain. 
   Makro `\inputsong` upravuje tokenizér TeXu tak, že lze písničky zapisovat v čistém textu s minimem speciálního formátování.
   Syntaxe je popsaná v `JakPsatZpevnik-utf8.txt` 
   
   
   

## TODO:

1. Aktuálně nefunguje kompilace s moderním `csplain`. Je potřeba zdrojáky `zpevnik.src` zkonvertovat do utf8 a 
   pak se zbavit konvertování mezi kódováními.

2. přesunout společné části (lyric.tex, diagramy akordů, makefile) do společného adresáře (započato v `common`)
   a z variant zpěvníku se tam odkazovat
   
3. Zprovoznit opět překlad a kouknout co aktuální zdroják dělá.

4. Opět od Toma dostat verzi z roku 2012 - asi jsem ji už měl, protože jsem si napsal poznámku, že se tam lyric.te neliší, 
   ale jsou tam nové písničky a některé naopak odstraněné.
   
5. Bylo by dobré mít písničky v samostatných souborech jako výchozí stav. A sestavování zpěvníku nedělat čistě automaticky. 
   Písničky do `songs` by se pouze přidávali, ale v hlavním souboru se nemusí použít. To umožňuje nezahazovat již napsané písničky, i když se zrovna nepoužijou.

6. bude potřeba odstranit automaticky tvořené soubory a přidat je do .gitignore

