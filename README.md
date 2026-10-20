# codemap

Mapa de funcoes de um projeto (HTML com JS embutido, Apps Script .gs, JS/TS, Python, C# e outros) para fazer alteracoes lendo so as linhas necessarias.

Usa a extracao de sintaxe do [graphify](https://github.com/Graphify-Labs/graphify) (`pip install graphifyy`). Nao usa LLM.

```bash
python3 cm.py <pasta>                  # mapa completo: funcao ini-fim >chama <chamada_por
python3 cm.py <pasta> -q "termo1,termo2"  # so o que cita os termos: funcoes, vizinhas, ids, css, linhas de texto
```

O cache fica em `<pasta>/.codemap/` e so e refeito quando algum arquivo muda.
