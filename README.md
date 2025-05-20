## Hvorfor
Kitos understøtter på nuværende tidspunkt ikke API drevet brugerstyring, så denne løsning viser et udsnit af data fra kitos som vi ikke har noget imod at vise til hele organisationen. 

## Topdesk:
- krav: S2505-541
- deployment: S2505-7363

## API docs

[Kitos API docs](https://os2web.atlassian.net/wiki/spaces/KITOS/pages/658145384/S+dan+kommer+du+igang)


## Filer 
`main.py` fetcher data fra Kitos API. Følgende felter bliver splejset sammen til 1 json fil.

- IT System (navn)
- Beskrivelse
- Leverandør fra kontrakt endpoint
- Relevante Organisationsenheder
- System administrator
- Referencer

`index.html` viser data ved hjælp af [datatables.net](https://datatables.net/)

