export interface Hidrometro {
  numero_hidrometro: string;
  matricula: string | null;
  endereco: string | null;
  bairro: string | null;
  economias: number;
  ativo: boolean;
  atualizado_em: string;
  meses_com_leitura: number;
  consumo_medio_12m: number | null;
  consumo_ultimo_mes: number | null;
}

export interface ConsumoMensal {
  ano_mes: string;
  volume_m3: number;
}
