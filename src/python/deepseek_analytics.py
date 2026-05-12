# CardioIA Conectada - Ir Além 2: Integração DeepSeek V4 Pro
# FIAP - 2TIAO - Grupo 15 - Bruno Gambarini (RM561517)
# Análise inteligente de sinais vitais usando DeepSeek V4 Pro API

import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict, List

# API Key via variável de ambiente (NÃO commitar)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-e278afe995b144bcbe55c4873cd22d2e")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-pro"  # Modelo pago com reasoning

def analisar_sinais_vitais(dados_paciente: Dict) -> Dict:
    """
    Envia dados de sinais vitais para o DeepSeek V4 Pro e recebe análise clínica.
    O modelo V4 Pro oferece reasoning avançado ideal para diagnósticos médicos.
    """
    prompt = f"""
Você é um cardiologista-IA especializado em análise de sinais vitais de pacientes monitorados por IoT.
Analise os seguintes dados e forneça um laudo estruturado:

DADOS DO PACIENTE:
- Temperatura: {dados_paciente.get('temperatura', 'N/A')}°C
- Umidade ambiente: {dados_paciente.get('umidade', 'N/A')}%
- Batimentos cardíacos: {dados_paciente.get('bpm', 'N/A')} BPM
- Timestamp: {dados_paciente.get('timestamp', 'N/A')}
- Status conexão: {dados_paciente.get('status', 'N/A')}

Responda EXATAMENTE neste formato JSON (sem texto adicional):
{{
    "nivel_risco": "NORMAL|ATENCAO|CRITICO",
    "bpm_analise": "sua analise dos batimentos em uma frase curta",
    "temperatura_analise": "sua analise da temperatura em uma frase curta",
    "recomendacao": "acao recomendada em uma frase curta",
    "probabilidade_evento_cardiaco": "0.0 a 1.0"
}}
"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "Você é um cardiologista-IA conciso e preciso. Responda apenas em JSON válido."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,  # Baixa temperatura para respostas mais determinísticas
        "max_tokens": 500
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        content = result["choices"][0]["message"]["content"]
        # Extrai o JSON da resposta (pode vir com ```json)
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    
    except requests.exceptions.Timeout:
        return {"nivel_risco": "ERRO", "recomendacao": "Timeout na API DeepSeek", "probabilidade_evento_cardiaco": "0"}
    except Exception as e:
        return {"nivel_risco": "ERRO", "recomendacao": f"Falha na analise: {str(e)[:50]}", "probabilidade_evento_cardiaco": "0"}

def projetar_tendencia(dados_historicos: List[Dict], evento_atual: Dict) -> Dict:
    """
    Usa DeepSeek V4 Pro com contexto histórico para projetar tendências futuras.
    Equivalente ao objetivo final do GDELT: cruzar passado + presente = previsão.
    """
    # Resume histórico (últimos 7 dias resumidos)
    resumo_historico = _resumir_historico(dados_historicos, dias=7)
    
    prompt = f"""
Você é um sistema de IA preditiva em cardiologia. Dado o histórico de 7 dias do paciente e 
um evento atual, projete a tendência para as próximas 24 horas.

HISTÓRICO (7 dias):
{resumo_historico}

EVENTO ATUAL:
- Temperatura: {evento_atual.get('temperatura', 'N/A')}°C
- BPM: {evento_atual.get('bpm', 'N/A')}
- Timestamp: {evento_atual.get('timestamp', 'N/A')}
- Status: {evento_atual.get('status', 'online')}

Responda EXATAMENTE neste JSON:
{{
    "tendencia_bpm": "ESTAVEL|SUBINDO|DESCENDO|INSTAVEL",
    "tendencia_temperatura": "ESTAVEL|SUBINDO|DESCENDO",
    "previsao_bpm_6h": "numero estimado",
    "previsao_bpm_24h": "numero estimado",
    "nivel_alerta": "NORMAL|ATENCAO|CRITICO",
    "justificativa": "uma frase explicando a projecao",
    "confianca": "0.0 a 1.0"
}}
"""

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "Você é um sistema de IA preditiva em cardiologia. Responda apenas em JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 500
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception:
        return {
            "tendencia_bpm": "INDETERMINADO",
            "tendencia_temperatura": "INDETERMINADO",
            "nivel_alerta": "ERRO_API",
            "justificativa": "Falha na chamada da API DeepSeek V4 Pro",
            "confianca": "0"
        }

def gerar_relatorio_paciente(dados_historicos: List[Dict], paciente_id: str = "PACIENTE-01") -> str:
    """
    Gera relatório clínico completo usando DeepSeek V4 Pro.
    Ideal para entregar ao médico responsável.
    """
    resumo = _resumir_historico(dados_historicos, dias=30)
    
    prompt = f"""
Gere um relatório clínico de monitoramento cardíaco para o paciente {paciente_id} 
com base nos seguintes dados de 30 dias:

{resumo}

Formato do relatório (use markdown):
1. RESUMO EXECUTIVO (2-3 frases)
2. ESTATÍSTICAS VITAIS (médias, máximos, mínimos detectados)
3. EVENTOS RELEVANTES (dias com anomalias)
4. TENDÊNCIA GERAL (melhora, piora, estável)
5. RECOMENDAÇÕES (2-3 ações sugeridas ao médico)
"""

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "Você é um cardiologista que gera relatórios de monitoramento IoT."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 1000
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"# ERRO NA GERAÇÃO DO RELATÓRIO\n\nFalha na API DeepSeek V4 Pro: {str(e)[:100]}"

def classificar_noticia_relacionada(noticia_titulo: str, dados_paciente: Dict) -> Dict:
    """
    Classifica se uma notícia (ex: RSS) tem relação com o monitoramento do paciente.
    Útil para o pipeline RSS ↔ GDELT ↔ CardioIA.
    """
    prompt = f"""
Analise se a seguinte notícia tem relação com o monitoramento cardíaco de um paciente.

NOTÍCIA: "{noticia_titulo}"

DADOS ATUAIS DO PACIENTE:
- BPM: {dados_paciente.get('bpm', 'N/A')}
- Temperatura: {dados_paciente.get('temperatura', 'N/A')}°C
- Timestamp: {dados_paciente.get('timestamp', 'N/A')}

Responda APENAS este JSON:
{{
    "tem_relacao": true/false,
    "categoria": "TECNOLOGIA|SAUDE|ECONOMIA|REGULACAO|OUTRO",
    "impacto_potencial": "POSITIVO|NEGATIVO|NEUTRO",
    "explicacao": "uma frase curta"
}}
"""
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "Você é um classificador de notícias para IoT médico. Responda apenas JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 200
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception:
        return {"tem_relacao": False, "categoria": "ERRO_API", "impacto_potencial": "NEUTRO", "explicacao": "Falha na API"}

def _resumir_historico(dados: List[Dict], dias: int = 7) -> str:
    """Resume dados históricos para o prompt do DeepSeek."""
    if not dados:
        return "Sem dados históricos disponíveis."

    temps = [d.get("temperatura", 0) for d in dados if d.get("temperatura")]
    bpms = [d.get("bpm", 0) for d in dados if d.get("bpm")]
    umids = [d.get("umidade", 0) for d in dados if d.get("umidade")]

    resumo = f"""
- Período: últimos {dias} dias ({len(dados)} amostras)
- Temperatura: min {min(temps):.1f}°C, max {max(temps):.1f}°C, media {sum(temps)/len(temps):.1f}°C
- BPM: min {min(bpms):.0f}, max {max(bpms):.0f}, media {sum(bpms)/len(bpms):.0f}
- Umidade: min {min(umids):.1f}%, max {max(umids):.1f}%, media {sum(umids)/len(umids):.1f}%
"""
    return resumo

# ============= TESTE =============
if __name__ == "__main__":
    print("=" * 60)
    print("  🫀 CardioIA — Integração DeepSeek V4 Pro")
    print("  Grupo 15 — Bruno Gambarini (RM561517)")
    print("=" * 60)

    # Teste: análise de sinais vitais
    paciente = {
        "temperatura": 38.5,
        "umidade": 62.0,
        "bpm": 125,
        "timestamp": datetime.now().isoformat(),
        "status": "online"
    }

    print("\n📊 Analisando sinais vitais com DeepSeek V4 Pro...")
    resultado = analisar_sinais_vitais(paciente)
    print(f"   ✅ Risco: {resultado.get('nivel_risco')}")
    print(f"   💓 BPM: {resultado.get('bpm_analise')}")
    print(f"   🌡️ Temp: {resultado.get('temperatura_analise')}")
    print(f"   🏥 Recomendação: {resultado.get('recomendacao')}")

    # Teste: classificação de notícia (pipeline RSS)
    print("\n📰 Classificando notícia RSS com DeepSeek V4 Pro...")
    noticia = "Apple corrige bug crítico no iPhone após 3 meses de investigação"
    classificacao = classificar_noticia_relacionada(noticia, paciente)
    print(f"   ✅ Tem relação: {classificacao.get('tem_relacao')}")
    print(f"   📂 Categoria: {classificacao.get('categoria')}")
    print(f"   📊 Impacto: {classificacao.get('impacto_potencial')}")

    print("\n" + "=" * 60)
    print("  ⚙️ Integração DeepSeek V4 Pro concluída!")
    print("  📌 Modelo: deepseek-v4-pro (API paga com reasoning)")
    print("  💰 Custo: $1.74/M input | $3.48/M output")
    print("=" * 60)
