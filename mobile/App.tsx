import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { BuscaScreen } from "./src/screens/BuscaScreen";
import { DetalheScreen } from "./src/screens/DetalheScreen";
import type { RootStackParamList } from "./src/navigation/types";

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="dark" />
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: "#0ea5e9" },
          headerTintColor: "#fff",
          headerTitleStyle: { fontWeight: "700" },
        }}
      >
        <Stack.Screen name="Busca" component={BuscaScreen} options={{ title: "Consulta de HD" }} />
        <Stack.Screen name="Detalhe" component={DetalheScreen} options={{ title: "Detalhe do HD" }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
