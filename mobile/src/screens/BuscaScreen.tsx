import { useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { buscarHidrometros } from "../lib/hidrometros";
import { StatusBadge } from "../components/StatusBadge";
import type { Hidrometro } from "../types/hd";
import type { RootStackParamList } from "../navigation/types";

type Props = NativeStackScreenProps<RootStackParamList, "Busca">;

export function BuscaScreen({ navigation }: Props) {
  const [termo, setTermo] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [resultados, setResultados] = useState<Hidrometro[]>([]);
  const [pesquisou, setPesquisou] = useState(false);

  async function pesquisar() {
    if (!termo.trim()) return;
    setCarregando(true);
    setErro(null);
    try {
      const dados = await buscarHidrometros(termo);
      setResultados(dados);
      setPesquisou(true);
      if (dados.length === 1) {
        navigation.navigate("Detalhe", { matricula: dados[0].matricula });
      }
    } catch (e) {
      setErro("Não foi possível consultar o HD. Verifique sua conexão e tente novamente.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <Text style={styles.titulo}>Consulta de HD</Text>
      <Text style={styles.subtitulo}>Digite a matrícula do hidrômetro para consultar</Text>

      <View style={styles.buscaRow}>
        <TextInput
          style={styles.input}
          placeholder="Ex: 123456"
          keyboardType="number-pad"
          value={termo}
          onChangeText={setTermo}
          onSubmitEditing={pesquisar}
          returnKeyType="search"
          autoFocus
        />
        <TouchableOpacity style={styles.botao} onPress={pesquisar} disabled={carregando}>
          {carregando ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.botaoTexto}>Buscar</Text>
          )}
        </TouchableOpacity>
      </View>

      {erro && <Text style={styles.erro}>{erro}</Text>}

      {pesquisou && !carregando && resultados.length === 0 && !erro && (
        <Text style={styles.vazio}>Nenhum HD encontrado com essa matrícula.</Text>
      )}

      <FlatList
        data={resultados}
        keyExtractor={(item) => item.matricula}
        contentContainerStyle={{ paddingTop: 8 }}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.item}
            onPress={() => navigation.navigate("Detalhe", { matricula: item.matricula })}
          >
            <View style={{ flex: 1 }}>
              <Text style={styles.itemMatricula}>HD {item.matricula}</Text>
              <Text style={styles.itemEndereco} numberOfLines={1}>
                {item.endereco ?? "Endereço não informado"}
              </Text>
            </View>
            <StatusBadge ativo={item.ativo} />
          </TouchableOpacity>
        )}
      />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc",
    paddingHorizontal: 20,
    paddingTop: 24,
  },
  titulo: {
    fontSize: 26,
    fontWeight: "800",
    color: "#0f172a",
  },
  subtitulo: {
    fontSize: 14,
    color: "#64748b",
    marginTop: 4,
    marginBottom: 20,
  },
  buscaRow: {
    flexDirection: "row",
    gap: 10,
  },
  input: {
    flex: 1,
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 18,
  },
  botao: {
    backgroundColor: "#0ea5e9",
    borderRadius: 12,
    paddingHorizontal: 20,
    justifyContent: "center",
    alignItems: "center",
    minWidth: 90,
  },
  botaoTexto: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 16,
  },
  erro: {
    color: "#dc2626",
    marginTop: 16,
  },
  vazio: {
    color: "#64748b",
    marginTop: 24,
    textAlign: "center",
  },
  item: {
    backgroundColor: "#fff",
    borderRadius: 14,
    padding: 16,
    marginBottom: 10,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  itemMatricula: {
    fontSize: 16,
    fontWeight: "700",
    color: "#0f172a",
  },
  itemEndereco: {
    fontSize: 13,
    color: "#64748b",
    marginTop: 2,
  },
});
