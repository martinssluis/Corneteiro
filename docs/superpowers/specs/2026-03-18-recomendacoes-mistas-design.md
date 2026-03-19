# Design: Recomendacoes Mistas Baseadas em Pontuacoes Anteriores

## Contexto

O projeto ja possui recomendacoes por custo-beneficio e por destaques da rodada, alem de servicos de historico e tendencia por atleta. A nova feature deve adicionar mais uma forma de recomendacao para o usuario final escolher, aproveitando o historico recente de pontuacoes para montar um ranking mais explicavel.

## Objetivo

Adicionar um novo criterio de recomendacao chamado `misto` dentro da experiencia existente de recomendacoes. Esse criterio deve combinar:

- fase recente
- consistencia
- custo-beneficio

O resultado deve ser um ranking de atletas ordenado por um `score_recomendacao`, com transparencia sobre como esse score foi formado.

## Fora de Escopo

- modelos estatisticos avancados ou machine learning
- personalizacao de pesos por usuario final
- alteracoes nos criterios ja existentes
- mudancas de interface visual

## Experiencia da API

### Contrato

Para suportar multiplos estilos no mesmo recurso, a API deve evoluir para um endpoint agregador:

`GET /recomendacoes`

Exemplo:

`GET /recomendacoes?criterio=misto&rodadas=5&limite=10&posicao_id=2`

As rotas dedicadas existentes, como custo-beneficio e destaques da rodada, podem continuar disponiveis por compatibilidade durante a transicao. O novo criterio `misto` deve entrar pelo endpoint agregador com selecao por query string.

### Parametros

- `criterio`: aceita os criterios existentes e o novo valor `misto`
- `rodadas`: opcional, inteiro entre 1 e 38, padrao `5`
- `limite`: opcional, inteiro entre 1 e 50, padrao `10`
- `posicao_id`: opcional, filtro por posicao

### Regras de validacao

- `criterio` e obrigatorio no endpoint `GET /recomendacoes`
- `criterio` invalido retorna `400`
- `rodadas` fora do intervalo retorna `400`
- `limite` fora do intervalo retorna `400`

## Formula do Ranking

### Componentes do score

O criterio `misto` deve calcular um ranking a partir de tres componentes normalizados na escala `0..10`:

1. `score_fase_recente`
   Usa a media das ultimas pontuacoes validas do atleta nas ultimas `N` rodadas consultadas.

2. `score_consistencia`
   Mede a estabilidade do atleta com base na oscilacao das pontuacoes recentes. Menor oscilacao significa nota maior.

3. `score_custo_beneficio`
   Mede o retorno em relacao ao preco atual, usando a relacao entre desempenho e `preco_num`.

### Normalizacao proposta

Para manter o planejamento objetivo, a implementacao deve seguir a regra abaixo como ponto de partida:

- `score_fase_recente`: normalizar a media recente do atleta entre os candidatos elegiveis da consulta
- `score_consistencia`: calcular uma medida de oscilacao recente e inverter a nota para que menor oscilacao gere valor maior
- `score_custo_beneficio`: normalizar o indice `media_num / preco_num` entre os candidatos elegiveis da consulta

Formula sugerida de normalizacao:

`nota_normalizada = 10 * (valor - minimo) / (maximo - minimo)`

Quando `maximo == minimo`, a nota do componente para todos os atletas deve ser `10`, evitando divisao por zero e mantendo comparabilidade.

### Pesos iniciais

- fase recente: `0.5`
- consistencia: `0.3`
- custo-beneficio: `0.2`

Esses pesos devem ficar centralizados na implementacao para permitir calibragem futura sem alterar o contrato da API.

### Perfil de risco

O comportamento aprovado para o criterio `misto` e o perfil `equilibrado`.

Regras do perfil:

- atletas com poucas partidas recentes ainda podem ser recomendados
- amostras pequenas devem sofrer penalizacao moderada
- o objetivo e reduzir o impacto de uma rodada isolada sem excluir oportunidades

### Penalizacao por amostra

A resposta deve expor uma `penalizacao_amostra` aplicada ao score final quando o atleta tiver poucas partidas validas.

Formula proposta para o perfil equilibrado:

- definir `rodadas_referencia` como o valor de `rodadas` da consulta
- calcular `fator_amostra = partidas_validas / rodadas_referencia`
- limitar `fator_amostra` ao intervalo `0..1`
- calcular `penalizacao_amostra = 0.5 * (1 - fator_amostra)`

Uso no score final:

`score_base = 0.5 * score_fase_recente + 0.3 * score_consistencia + 0.2 * score_custo_beneficio`

`score_recomendacao = score_base * (1 - penalizacao_amostra)`

Com essa regra:

- atleta com amostra completa recebe penalizacao zero
- atleta com metade da amostra recebe penalizacao moderada
- atleta com amostra muito pequena ainda pode aparecer, mas perde competitividade

## Elegibilidade dos Atletas

Para entrar no ranking:

- o atleta precisa existir no mercado atual
- `preco_num` deve ser valido e maior que zero
- o historico deve considerar apenas partidas com `entrou_em_campo=True`

Atletas sem historico aproveitavel podem ser excluidos do ranking. Atletas com poucas partidas validas podem permanecer, desde que a penalizacao equilibrada seja aplicada.

## Fluxo Interno

1. Buscar atletas do mercado atual
2. Aplicar filtro por `posicao_id`, quando informado
3. Para cada atleta elegivel, carregar o historico recente
4. Extrair `ultimas_pontuacoes` usando apenas partidas validas
5. Calcular os tres componentes do score
6. Aplicar a penalizacao de amostra pequena
7. Gerar `score_recomendacao`
8. Ordenar atletas por `score_recomendacao` em ordem decrescente
9. Retornar apenas os `top N` definidos por `limite`

## Estrutura Sugerida de Implementacao

### Servicos

- `historico_service` continua como fonte do historico bruto
- `recomendacoes_service` passa a orquestrar o novo criterio `misto`

### Responsabilidades novas em `recomendacoes_service`

- validar e rotear o `criterio`
- montar o ranking do criterio `misto`
- calcular os componentes do score
- aplicar a penalizacao equilibrada
- retornar metadados e explicacao do ranking

Se a implementacao atual de rotas estiver segmentada por endpoint dedicado, a recomendacao mista pode nascer em um endpoint existente de recomendacoes, desde que o criterio seja selecionado via query string para suportar multiplas estrategias no mesmo recurso.

## Formato da Resposta

Exemplo de payload:

```json
{
  "criterio": "misto",
  "perfil": "equilibrado",
  "rodadas": 5,
  "posicao_id": 2,
  "limite": 10,
  "quantidade": 10,
  "recomendacoes": [
    {
      "atleta_id": 123,
      "apelido": "Jogador X",
      "clube_id": 10,
      "posicao_id": 2,
      "preco_num": 14.5,
      "media_num": 6.2,
      "partidas_validas": 4,
      "ultimas_pontuacoes": [5.4, 7.1, 6.3, 8.0],
      "score_fase_recente": 8.1,
      "score_consistencia": 7.0,
      "score_custo_beneficio": 6.4,
      "penalizacao_amostra": 0.1,
      "score_recomendacao": 6.69
    }
  ]
}
```

### Requisitos do payload

- expor o criterio escolhido
- expor o perfil utilizado
- expor configuracoes relevantes como `rodadas`, `limite` e `posicao_id`
- explicar o ranking por atleta com os componentes do score
- manter uma resposta vazia valida quando nao houver atletas elegiveis

## Tratamento de Erros

- `400` para `criterio` invalido
- `400` para `rodadas` invalido
- `400` para `limite` invalido
- resposta com lista vazia quando nao houver atletas elegiveis para o criterio e filtros informados

## Impacto na Evolucao do Produto

Essa mudanca prepara o endpoint de recomendacoes para suportar varios estilos de recomendacao escolhidos pelo usuario final. O criterio `misto` entra como uma estrategia adicional, sem substituir os criterios atuais.

Isso cria uma base para futuras recomendacoes com variacoes como:

- maior foco em tendencia
- maior foco em seguranca
- maior foco em upside

Sem exigir mudanca no modelo mental do consumidor da API.

## Testes Recomendados

- calcula ranking misto com historico suficiente
- aplica penalizacao moderada para pouca amostra
- ignora atletas sem `preco_num` valido
- respeita filtro por `posicao_id`
- respeita `limite`
- ordena por `score_recomendacao` em ordem decrescente
- retorna lista vazia sem erro quando nao houver recomendados
- valida `criterio`, `rodadas` e `limite`

## Riscos e Decisoes em Aberto para a Implementacao

- A medida exata de oscilacao usada em `score_consistencia` deve ser escolhida na implementacao. O minimo esperado e uma metrica simples e previsivel, como amplitude ou desvio medio, sem aumentar a complexidade do criterio.
- Se houver necessidade de compatibilidade com consumidores atuais, a implementacao pode manter rotas antigas e adicionar a nova selecao por `criterio` sem quebra de contrato.
