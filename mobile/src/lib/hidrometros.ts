import { supabase } from "./supabase";
import type { ConsumoMensal, Hidrometro } from "../types/hd";

export async function buscarHidrometros(termo: string): Promise<Hidrometro[]> {
  const matricula = termo.trim();
  if (!matricula) return [];

  const { data, error } = await supabase
    .from("hidrometros_resumo")
    .select("*")
    .ilike("matricula", `%${matricula}%`)
    .order("matricula", { ascending: true })
    .limit(30);

  if (error) throw error;
  return (data ?? []) as Hidrometro[];
}

export async function buscarConsumoDoHd(matricula: string): Promise<ConsumoMensal[]> {
  const doze_meses_atras = new Date();
  doze_meses_atras.setMonth(doze_meses_atras.getMonth() - 11);
  doze_meses_atras.setDate(1);

  const { data, error } = await supabase
    .from("consumos")
    .select("ano_mes, volume_m3")
    .eq("matricula", matricula)
    .gte("ano_mes", doze_meses_atras.toISOString().slice(0, 10))
    .order("ano_mes", { ascending: false });

  if (error) throw error;
  return (data ?? []) as ConsumoMensal[];
}
