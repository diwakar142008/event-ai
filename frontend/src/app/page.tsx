import { EventoraProvider } from "@/components/eventora-provider";
import { Dashboard } from "@/components/dashboard";

export default function HomePage() {
  return (
    <EventoraProvider>
      <Dashboard />
    </EventoraProvider>
  );
}
