import { EventoraProvider } from "@/components/eventora-provider";
import { InsightsWorkspace } from "@/components/insights-workspace";

export default function InsightsPage() {
  return (
    <EventoraProvider>
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <InsightsWorkspace />
      </div>
    </EventoraProvider>
  );
}
