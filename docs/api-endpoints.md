# Documentacao da API

## Visao Geral

Esta API organiza os endpoints por recurso:

- `mercado`: status geral do mercado
- `atletas`: consulta de atletas e busca por nome
- `pontuados`: pontuacoes da rodada atual ou de rodadas especificas
- `clubes`: lista e busca de clubes
- `historico`: historico recente de pontuacao por atleta
- `tendencia`: analise de tendencia de desempenho por atleta
- `recomendacoes`: estrategias de recomendacao de jogadores

Se a aplicacao estiver rodando localmente, os exemplos abaixo assumem a base:

```text
http://localhost:5000
```

## Como Navegar Pela API

Ordem sugerida para exploracao:

1. Consultar `GET /mercado/status` para entender a rodada atual
2. Usar `GET /atletas/buscar?nome=...` para encontrar IDs de atletas
3. Consultar `GET /atletas/{id}` para detalhes do atleta
4. Explorar `GET /pontuados` ou `GET /pontuados/{rodada}` para desempenho em rodada
5. Usar `GET /historico/atleta/{id}` para retrospecto recente
6. Usar `GET /tendencia/atleta/{id}` para ver momento do atleta
7. Usar `GET /recomendacoes` para rankings prontos por criterio

## Padrao de Erros

Os erros normalmente seguem este formato:

```json
{
  "erro": "Mensagem descritiva"
}
```

Em alguns casos, tambem pode existir:

```json
{
  "erro": "Mensagem descritiva",
  "detalhe": "Informacao adicional"
}
```

## Mercado

### `GET /mercado/status`

Retorna o status atual do mercado do Cartola, incluindo informacoes como rodada atual e estado do mercado.

Exemplo:

```http
GET /mercado/status
```

Informacoes obtidas:

- status do mercado
- rodada atual
- configuracoes retornadas pela API base do Cartola

## Atletas

### `GET /atletas/status`

Replica o status do mercado pelo modulo de atletas.

Exemplo:

```http
GET /atletas/status
```

Informacoes obtidas:

- status do mercado
- rodada atual

### `GET /atletas/{atleta_id}`

Busca um atleta por ID.

Exemplo:

```http
GET /atletas/12345
```

Informacoes obtidas:

- dados brutos do atleta
- clube enriquecido
- posicao enriquecida

Retornos comuns:

- `200` se encontrar o atleta
- `404` se o atleta nao existir

### `GET /atletas/buscar?nome={nome}&exato={true|false}`

Busca atletas por nome, apelido ou slug.

Exemplos:

```http
GET /atletas/buscar?nome=arrascaeta
GET /atletas/buscar?nome=arrascaeta&exato=true
```

Parametros:

- `nome`: obrigatorio
- `exato`: opcional, padrao `false`

Informacoes obtidas:

- termo pesquisado
- quantidade de atletas encontrados
- lista de atletas correspondentes

Observacao:

- a lista nao vem enriquecida com clube e posicao por padrao, para reduzir custo da consulta

## Pontuados

### `GET /pontuados`

Lista os pontuados da rodada atual.

Exemplos:

```http
GET /pontuados
GET /pontuados?calcular=true
```

Parametros:

- `calcular`: opcional, `true` ou `false`

Informacoes obtidas:

- mapa de atletas pontuados na rodada atual
- scout de cada atleta
- opcionalmente `pontuacao_calculada`, quando `calcular=true`

### `GET /pontuados/{rodada}`

Lista os pontuados de uma rodada especifica.

Exemplos:

```http
GET /pontuados/10
GET /pontuados/10?calcular=true
```

Informacoes obtidas:

- mapa de atletas pontuados na rodada informada
- scout de cada atleta
- opcionalmente `pontuacao_calculada`

### `GET /pontuados/atleta/{atleta_id}`

Busca a pontuacao de um atleta na rodada atual.

Exemplos:

```http
GET /pontuados/atleta/12345
GET /pontuados/atleta/12345?calcular=false
```

Parametros:

- `calcular`: opcional, padrao `true`

Informacoes obtidas:

- `atleta_id`
- `apelido`
- `foto`
- `pontuacao_cartola`
- `pontuacao_calculada`, se habilitada
- `scout`
- `entrou_em_campo`
- clube enriquecido
- posicao enriquecida

### `GET /pontuados/{rodada}/atleta/{atleta_id}`

Busca a pontuacao de um atleta em uma rodada especifica.

Exemplos:

```http
GET /pontuados/10/atleta/12345
GET /pontuados/10/atleta/12345?calcular=true
```

Informacoes obtidas:

- numero da rodada
- dados da pontuacao do atleta naquela rodada
- clube enriquecido
- posicao enriquecida

## Clubes

### `GET /clubes`

Lista todos os clubes disponiveis.

Exemplo:

```http
GET /clubes
```

Informacoes obtidas:

- colecao de clubes com identificadores e metadados

### `GET /clubes/{clube_id}`

Busca um clube por ID.

Exemplo:

```http
GET /clubes/262
```

Informacoes obtidas:

- dados do clube

### `GET /clubes/buscar?slug={slug}`

Busca um clube pelo slug.

Exemplo:

```http
GET /clubes/buscar?slug=flamengo
```

Parametros:

- `slug`: obrigatorio

Informacoes obtidas:

- dados do clube correspondente ao slug

## Historico

### `GET /historico/atleta/{atleta_id}?rodadas={n}`

Retorna o historico recente de um atleta com base nas ultimas rodadas disponiveis.

Exemplos:

```http
GET /historico/atleta/12345
GET /historico/atleta/12345?rodadas=8
```

Parametros:

- `rodadas`: opcional, padrao `5`, intervalo `1..38`

Informacoes obtidas:

- `atleta_id`
- `rodadas_analisadas`
- lista `historico`

Para cada item do historico:

- `rodada`
- `pontuacao_cartola`
- `pontuacao_calculada`
- `scout`
- `entrou_em_campo`
- `clube_id`
- `posicao_id`

## Tendencia

### `GET /tendencia/atleta/{atleta_id}?rodadas={n}`

Calcula a tendencia recente de desempenho do atleta.

Exemplos:

```http
GET /tendencia/atleta/12345
GET /tendencia/atleta/12345?rodadas=6
```

Parametros:

- `rodadas`: opcional, padrao `6`, intervalo `1..38`

Informacoes obtidas:

- `atleta_id`
- `rodadas_consideradas`
- `partidas_validas`
- `ultimas_pontuacoes`
- `media_bloco_antigo`
- `media_bloco_recente`
- `variacao`
- `tendencia`

Valores esperados de `tendencia`:

- `alta`
- `queda`
- `estavel`
- `insuficiente`

## Recomendacoes

### `GET /recomendacoes?criterio={criterio}`

Endpoint agregador de recomendacoes. O parametro `criterio` e obrigatorio.

Exemplos:

```http
GET /recomendacoes?criterio=custo_beneficio
GET /recomendacoes?criterio=destaques_rodada&rodada=10
GET /recomendacoes?criterio=misto&rodadas=5&limite=10&posicao_id=2
GET /recomendacoes?criterio=confronto_hibrido&janela_curta=5&janela_longa=10&peso_curta=0.7&peso_longa=0.3&limite=10&posicao_id=2
```

Parametros gerais:

- `criterio`: obrigatorio
- `posicao_id`: opcional
- `limite`: opcional, padrao `10`, intervalo `1..50`

Criterios suportados:

- `custo_beneficio`
- `destaques_rodada`
- `misto`
- `confronto_hibrido`

### `criterio=custo_beneficio`

Ranking simples por relacao entre media e preco.

Informacoes obtidas:

- criterio usado
- posicao filtrada, se houver
- limite aplicado
- quantidade retornada
- lista de recomendacoes com:
- `atleta_id`
- `apelido`
- `clube_id`
- `clube_nome`
- `clube_sigla`
- `posicao_id`
- `posicao_nome`
- `preco_num`
- `media_num`
- `indice_custo_beneficio`

### `criterio=destaques_rodada`

Ranking dos destaques da rodada atual ou de uma rodada especifica.

Parametros extras:

- `rodada`: opcional
- `ordenar_por`: opcional, `pontuacao_cartola` ou `pontuacao_calculada`

Informacoes obtidas:

- criterio usado
- rodada analisada
- ordenacao aplicada
- lista de atletas com pontuacao e scout

### `criterio=misto`

Ranking de recomendacao baseado em:

- fase recente
- consistencia
- custo-beneficio

Parametros extras:

- `rodadas`: opcional, padrao `5`, intervalo `1..38`

Informacoes obtidas:

- `criterio`
- `perfil`
- `rodadas`
- `posicao_id`
- `limite`
- `quantidade`
- lista `recomendacoes`

Para cada recomendacao:

- `atleta_id`
- `apelido`
- `clube_id`
- `clube_nome`
- `clube_sigla`
- `posicao_id`
- `posicao_nome`
- `preco_num`
- `media_num`
- `partidas_validas`
- `ultimas_pontuacoes`
- `score_fase_recente`
- `score_consistencia`
- `score_custo_beneficio`
- `penalizacao_amostra`
- `score_recomendacao`

### `criterio=confronto_hibrido`

Ranking que combina momento individual do atleta com contexto do confronto da rodada.

Parametros extras:

- `janela_curta`: opcional, padrao `5`, intervalo `1..38`
- `janela_longa`: opcional, padrao `10`, intervalo `1..38`
- `peso_curta`: opcional, padrao `0.7`, intervalo `0..1`
- `peso_longa`: opcional, padrao `0.3`, intervalo `0..1`

Regras:

- `peso_curta + peso_longa` deve ser igual a `1.0`
- historico do confronto considera recorte por posicao do atleta

Informacoes obtidas:

- `criterio`
- `janela_curta`
- `janela_longa`
- `peso_curta`
- `peso_longa`
- `posicao_id`
- `limite`
- `quantidade`
- lista `recomendacoes`

Para cada recomendacao:

- `atleta_id`
- `apelido`
- `clube_id`
- `clube_nome`
- `clube_sigla`
- `posicao_id`
- `posicao_nome`
- `adversario_id`
- `adversario_nome`
- `adversario_sigla`
- `preco_num`
- `media_num`
- `historico_time_curto`
- `historico_time_longo`
- `score_individual`
- `score_confronto_curto`
- `score_confronto_longo`
- `forca_confronto`
- `score_recomendacao`

### Endpoints legados de recomendacao

Os endpoints abaixo continuam disponiveis:

- `GET /recomendacoes/custo-beneficio`
- `GET /recomendacoes/destaques-rodada`

Eles seguem a mesma ideia dos criterios equivalentes no endpoint agregador e podem ser mantidos por compatibilidade.

## Exemplos de Fluxos Reais

### Descobrir um atleta e analisar desempenho

1. Buscar por nome:

```http
GET /atletas/buscar?nome=hulk
```

2. Pegar o ID retornado e consultar detalhes:

```http
GET /atletas/12345
```

3. Consultar historico recente:

```http
GET /historico/atleta/12345?rodadas=5
```

4. Consultar tendencia:

```http
GET /tendencia/atleta/12345?rodadas=6
```

### Encontrar boas recomendacoes para escalar

1. Ver ranking por custo-beneficio:

```http
GET /recomendacoes?criterio=custo_beneficio&posicao_id=2&limite=10
```

2. Ver ranking misto:

```http
GET /recomendacoes?criterio=misto&posicao_id=2&rodadas=5&limite=10
```

3. Ver confronto hibrido da rodada:

```http
GET /recomendacoes?criterio=confronto_hibrido&posicao_id=2&janela_curta=5&janela_longa=10&peso_curta=0.7&peso_longa=0.3&limite=10
```

4. Comparar com destaques de rodada:

```http
GET /recomendacoes?criterio=destaques_rodada&rodada=10&limite=10
```
