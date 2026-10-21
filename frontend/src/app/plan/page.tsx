import { EventoraProvider } from "@/components/eventora-provider";
import { PlanWorkspace } from "@/components/plan-workspace";

export default function PlanPage() {
  return (
    <EventoraProvider>
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <PlanWorkspace />
      </div>
    </EventoraProvider>
  );
}
