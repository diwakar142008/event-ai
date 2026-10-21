import { EventoraProvider } from "@/components/eventora-provider";
import { Dashboard } from "@/components/dashboard";

export default function HomePage() {
  return (
    <EventoraProvider>
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <Dashboard />
      </div>
    </EventoraProvider>
  );
}
