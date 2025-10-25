# Guia de Criação de Regras (DSL)

As regras são descritas em YAML e suportam composição entre baseline global e overrides por organização.

## Estrutura

```yaml
- id: ZFM-ST-001
  name: "Produto sujeito a ST sem destaque; ZFM"
  when:
    all:
      - item.uf_dest == "AM"
      - item.zfm == true
      - item.cst in ["10","60"]
      - not item.icms_st_destacado
  then:
    inconsistency_code: "ST_MISSING"
    severity: "high"
    message_pt: "Produto possivelmente sujeito a ST sem destaque na entrada."
    suggestion_code: "ST_RATEIO"
    references:
      - "Convênio ICMS 142/2018"
      - "Regulamento ICMS/AM - art. 111"
```

As expressões aceitam operadores booleanos (`all`, `any`, `not`) e funções auxiliares (`is_zfm`, `has_mva`, `cfop_is`).
