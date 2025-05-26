## Hvorfor vise et overblik over systemer når Kitos gør det?
Fordi man i digitalisering ikke ønsker at oprette alle i Kitos. Det ville være en administrativ byrde. 

## Topdesk:
- krav: S2505-541
- deployment: S2505-7363

## API docs

[Kitos API docs](https://os2web.atlassian.net/wiki/spaces/KITOS/pages/658145384/S+dan+kommer+du+igang)


## Docs 
`main.py` fetcher data fra Kitos API. Følgende felter bliver splejset sammen til 1 json fil.

- IT System (navn)
- Beskrivelse
- Leverandør fra kontrakt endpoint
- Relevante Organisationsenheder
- System administrator
- Referencer

`index.html` viser data ved hjælp af [datatables.net](https://datatables.net/) samt en fetch timestamp. 