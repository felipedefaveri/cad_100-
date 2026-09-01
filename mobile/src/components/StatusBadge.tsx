import { StyleSheet, Text, View } from "react-native";

export function StatusBadge({ ativo }: { ativo: boolean }) {
  return (
    <View style={[styles.badge, ativo ? styles.ativo : styles.inativo]}>
      <Text style={styles.texto}>{ativo ? "ATIVO" : "INATIVO"}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    alignSelf: "flex-start",
  },
  ativo: {
    backgroundColor: "#dcfce7",
  },
  inativo: {
    backgroundColor: "#fee2e2",
  },
  texto: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
});
