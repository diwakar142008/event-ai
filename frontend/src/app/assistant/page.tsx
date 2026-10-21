import { EventoraProvider } from "@/components/eventora-provider";
import { AssistantWorkspace } from "@/components/assistant-workspace";

export default function AssistantPage() {
  return (
    <EventoraProvider>
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <AssistantWorkspace />
      </div>
    </EventoraProvider>
  );
}
