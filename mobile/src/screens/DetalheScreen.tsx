import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { buscarConsumoDoHd, buscarHidrometros } from "../lib/hidrometros";
import { StatusBadge } from "../components/StatusBadge";
import type { ConsumoMensal, Hidrometro } from "../types/hd";
import type { RootStackParamList } from "../navigation/types";

type Props = NativeStackScreenProps<RootStackParamList, "Detalhe">;

const MESES = [
  "jan", "fev", "mar", "abr", "mai", "jun",
  "jul", "ago", "set", "out", "nov", "dez",
];

function formatarMes(anoMes: string) {
  const [ano, mes] = anoMes.split("-");
  return `${MESES[Number(mes) - 1]}/${ano.slice(2)}`;
}

export function DetalheScreen({ route, navigation }: Props) {
  const { matricula } = route.params;
  const [hd, setHd] = useState<Hidrometro | null>(null);
  const [consumos, setConsumos] = useState<ConsumoMensal[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  async function carregar() {
    setErro(null);
    try {
      const [hidrometros, historico] = await Promise.all([
        buscarHidrometros(matricula),
        buscarConsumoDoHd(matricula),
      ]);
      const encontrado = hidrometros.find((h) => h.matricula === matricula) ?? hidrometros[0] ?? null;
      setHd(encontrado);
      setConsumos(historico);
    } catch (e) {
      setErro("Não foi possível carregar os dados do HD.");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    navigation.setOptions({ title: `HD ${matricula}` });
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matricula]);

  if (carregando) {
    return (
      <View style={styles.centro}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (erro || !hd) {
    return (
      <View style={styles.centro}>
        <Text style={styles.erro}>{erro ?? "HD não encontrado."}</Text>
      </View>
    );
  }

  const maiorVolume = Math.max(1, ...consumos.map((c) => c.volume_m3));

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ padding: 20 }}
      refreshControl={<RefreshControl refreshing={false} onRefresh={carregar} />}
    >
      <View style={styles.cabecalho}>
        <Text style={styles.matricula}>HD {hd.matricula}</Text>
        <StatusBadge ativo={hd.ativo} />
      </View>
      <Text style={styles.endereco}>{hd.endereco ?? "Endereço não informado"}</Text>
      {hd.bairro && <Text style={styles.bairro}>{hd.bairro}</Text>}

      <View style={styles.cardsRow}>
        <View style={styles.card}>
          <Text style={styles.cardValor}>{hd.economias}</Text>
          <Text style={styles.cardLabel}>economias</Text>
        </View>
        <View style={styles.card}>
          <Text style={styles.cardValor}>
            {hd.consumo_medio_12m != null ? hd.consumo_medio_12m.toFixed(1) : "—"}
          </Text>
          <Text style={styles.cardLabel}>média m³/mês (12m)</Text>
        </View>
        <View style={styles.card}>
          <Text style={styles.cardValor}>
            {hd.consumo_ultimo_mes != null ? hd.consumo_ultimo_mes.toFixed(1) : "—"}
          </Text>
          <Text style={styles.cardLabel}>último mês (m³)</Text>
        </View>
      </View>

      <Text style={styles.secaoTitulo}>Consumo — últimos 12 meses</Text>

      {consumos.length === 0 ? (
        <Text style={styles.semDados}>Sem histórico de consumo cadastrado para este HD.</Text>
      ) : (
        <View style={styles.historico}>
          {consumos.map((c) => (
            <View key={c.ano_mes} style={styles.linhaHistorico}>
              <Text style={styles.mesLabel}>{formatarMes(c.ano_mes)}</Text>
              <View style={styles.barraFundo}>
                <View
                  style={[
                    styles.barraPreenchida,
                    { width: `${(c.volume_m3 / maiorVolume) * 100}%` },
                  ]}
                />
              </View>
              <Text style={styles.volumeLabel}>{c.volume_m3.toFixed(1)}</Text>
            </View>
          ))}
        </View>
      )}

      <Text style={styles.atualizadoEm}>
        Cadastro atualizado em {new Date(hd.atualizado_em).toLocaleDateString("pt-BR")}
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc",
  },
  centro: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  erro: {
    color: "#dc2626",
    fontSize: 16,
    textAlign: "center",
  },
  cabecalho: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  matricula: {
    fontSize: 24,
    fontWeight: "800",
    color: "#0f172a",
  },
  endereco: {
    fontSize: 15,
    color: "#334155",
    marginTop: 6,
  },
  bairro: {
    fontSize: 13,
    color: "#64748b",
  },
  cardsRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 20,
  },
  card: {
    flex: 1,
    backgroundColor: "#fff",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    paddingVertical: 16,
    alignItems: "center",
  },
  cardValor: {
    fontSize: 22,
    fontWeight: "800",
    color: "#0ea5e9",
  },
  cardLabel: {
    fontSize: 11,
    color: "#64748b",
    marginTop: 4,
    textAlign: "center",
  },
  secaoTitulo: {
    fontSize: 16,
    fontWeight: "700",
    color: "#0f172a",
    marginTop: 28,
    marginBottom: 12,
  },
  semDados: {
    color: "#64748b",
  },
  historico: {
    gap: 10,
  },
  linhaHistorico: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  mesLabel: {
    width: 42,
    fontSize: 12,
    color: "#475569",
  },
  barraFundo: {
    flex: 1,
    height: 10,
    backgroundColor: "#e2e8f0",
    borderRadius: 999,
    overflow: "hidden",
  },
  barraPreenchida: {
    height: "100%",
    backgroundColor: "#0ea5e9",
    borderRadius: 999,
  },
  volumeLabel: {
    width: 44,
    fontSize: 12,
    color: "#334155",
    textAlign: "right",
  },
  atualizadoEm: {
    marginTop: 24,
    fontSize: 11,
    color: "#94a3b8",
    textAlign: "center",
  },
});
