import json
import os
from datetime import datetime
from typing import List, Optional, Dict
from models import Trecho, Manutencao, DadosClimaticos


class DatabaseSimulada:
    
    def __init__(self):
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, '..', 'data')
        
        trechos_path = os.path.join(data_dir, 'trechos.json')
        with open(trechos_path, 'r', encoding='utf-8') as f:
            self.trechos = json.load(f)
        
        manutencoes_path = os.path.join(data_dir, 'manutencoes.json')
        with open(manutencoes_path, 'r', encoding='utf-8') as f:
            self.manutencoes = json.load(f)
        
        clima_path = os.path.join(data_dir, 'clima.json')
        with open(clima_path, 'r', encoding='utf-8') as f:
            self.clima = json.load(f)
        
        print(f"✓ Database carregado: {len(self.trechos)} trechos, "
              f"{len(self.manutencoes)} manutenções, "
              f"{len(self.clima)} dias de clima")
    
    def get_trecho(self, trecho_id: int) -> Optional[Dict]:
        for trecho in self.trechos:
            if trecho['id'] == trecho_id:
                return trecho
        return None
    
    def get_todos_trechos(self) -> List[Dict]:
        return self.trechos
    
    def get_manutencoes_trecho(self, trecho_id: int) -> List[Dict]:
        return [m for m in self.manutencoes if m['trecho_id'] == trecho_id]
    
    def get_ultima_manutencao(self, trecho_id: int) -> Optional[Dict]:
        manutencoes = self.get_manutencoes_trecho(trecho_id)
        
        if not manutencoes:
            return None
        
        return max(manutencoes, key=lambda m: datetime.strptime(m['data'], '%Y-%m-%d'))
    
    def get_dias_desde_manutencao(self, trecho_id: int) -> int:
        ultima = self.get_ultima_manutencao(trecho_id)
        
        if ultima is None:
            return 999
        
        data_manutencao = datetime.strptime(ultima['data'], '%Y-%m-%d')
        data_hoje = datetime.now()
        dias = (data_hoje - data_manutencao).days
        
        return dias
    
    def get_clima_atual(self) -> Optional[Dict]:
        if not self.clima:
            return None
        
        return max(self.clima, key=lambda c: c['data'])
    
    def get_clima_por_data(self, data_str: str) -> Optional[Dict]:
        for clima in self.clima:
            if clima['data'] == data_str:
                return clima
        return None
    
    def get_custo_total_manutencoes(self, trecho_id: int) -> float:
        manutencoes = self.get_manutencoes_trecho(trecho_id)
        return sum(m['custo'] for m in manutencoes)
    
    def get_quantidade_manutencoes(self, trecho_id: int) -> int:
        return len(self.get_manutencoes_trecho(trecho_id))


try:
    db = DatabaseSimulada()
    print("✓ Database inicializado com sucesso!\n")
except Exception as e:
    print(f"❌ Erro ao inicializar database: {e}")
    print("Verifique se os arquivos JSON estão na pasta 'data/'")
    db = None


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTE DO DATABASE")
    print("="*60 + "\n")
    
    if db is None:
        print("❌ Database não inicializado")
    else:
        print("📍 TESTE 1: Trechos Carregados")
        print("-" * 60)
        for trecho in db.get_todos_trechos():
            print(f"  {trecho['id']}: {trecho['nome']} (km {trecho['km_inicio']}-{trecho['km_fim']})")
        print()
        
        print("🔧 TESTE 2: Últimas Manutenções")
        print("-" * 60)
        for trecho in db.get_todos_trechos():
            ultima = db.get_ultima_manutencao(trecho['id'])
            dias = db.get_dias_desde_manutencao(trecho['id'])
            
            if ultima:
                print(f"  Trecho {trecho['id']}: {ultima['data']} ({dias} dias atrás)")
            else:
                print(f"  Trecho {trecho['id']}: Nunca foi mantido!")
        print()
        
        print("🌤️  TESTE 3: Clima Atual")
        print("-" * 60)
        clima = db.get_clima_atual()
        if clima:
            print(f"  Data: {clima['data']}")
            print(f"  Temperatura: {clima['temperatura_media']}°C")
            print(f"  Chuva: {clima['chuva_mm']}mm")
            print(f"  Umidade: {clima['umidade']}%")
        print()
        
        print("💰 TESTE 4: Custo Total por Trecho")
        print("-" * 60)
        for trecho in db.get_todos_trechos()[:3]:
            custo = db.get_custo_total_manutencoes(trecho['id'])
            qtd = db.get_quantidade_manutencoes(trecho['id'])
            print(f"  Trecho {trecho['id']}: R$ {custo:.2f} ({qtd} manutenções)")
        print()
        
        print("✅ Testes concluídos!")